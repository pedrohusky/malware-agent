import sys
import time
import binascii
import struct
import collections
import logging
import socket
import functools
import threading
import traceback
import warnings

try:
    import selectors
    from selectors import EVENT_READ, EVENT_WRITE

    EVENT_READ_WRITE = EVENT_READ | EVENT_WRITE
except ImportError:
    import select

    warnings.warn('selectors module not available, fallback to select')
    selectors = None

try:
    # for pycharm type hinting
    from typing import Union, Callable
except:
    pass

# socket recv buffer, 16384 bytes
RECV_BUFFER_SIZE = 2 ** 14

# default secretkey, use -k/--secretkey to change
SECRET_KEY = None  # "shootback"

# how long a SPARE slaver would keep
# once slaver received an heart-beat package from master,
#   the TTL would be reset. And heart-beat delay is less than TTL,
#   so, theoretically, spare slaver never timeout,
#   except network failure
# notice: working slaver would NEVER timeout
SPARE_SLAVER_TTL = 300

# internal program version, appears in CtrlPkg
INTERNAL_VERSION = 0x0013

# # how many packet are buffed, before delaying recv
# SOCKET_BRIDGE_SEND_BUFF_SIZE = 5

# version for human readable
__version__ = (2, 6, 1, INTERNAL_VERSION)

# just a logger
log = logging.getLogger(__name__)


def version_info():
    """get program version for human. eg: "2.1.0-r2" """
    return "{}.{}.{}-r{}".format(*__version__)


def configure_logging(level):
    logging.basicConfig(
        level=level,
        format='[%(levelname)s %(asctime)s] %(message)s',
    )


def fmt_addr(socket):
    """(host, int(port)) --> "host:port" """
    return "{}:{}".format(*socket)


def split_host(x):
    """ "host:port" --> (host, int(port))"""
    try:
        host, port = x.split(":")
        port = int(port)
    except:
        raise ValueError(
            "wrong syntax, format host:port is "
            "required, not {}".format(x))
    else:
        return host, port


def try_close(closable):
    """try close something

    same as
        try:
            connection.close()
        except:
            pass
    """
    try:
        closable.close()
    except:
        pass


def select_recv(conn, buff_size, timeout=None):
    """add timeout for socket.recv()
    :type conn: socket.socket
    :type buff_size: int
    :type timeout: float
    :rtype: Union[bytes, None]
    """
    if selectors:
        sel = selectors.DefaultSelector()
        sel.register(conn, EVENT_READ)
        events = sel.select(timeout)
        sel.close()
        if not events:
            # timeout
            raise RuntimeError("recv timeout")
    else:
        rlist, _, _ = select.select([conn], [], [], timeout)

    buff = conn.recv(buff_size)
    if not buff:
        raise RuntimeError("received zero bytes, socket was closed")

    return buff


def set_secretkey(key):
    global SECRET_KEY
    SECRET_KEY = key
    CtrlPkg.recalc_crc32()


class SocketBridge(object):
    """
    transfer data between sockets
    """

    def __init__(self):
        self.conn_rd = set()  # record readable-sockets
        self.conn_wr = set()  # record writeable-sockets
        self.map = {}  # record sockets pairs
        self.callbacks = {}  # record callbacks
        self.send_buff = {}  # buff one packet for those sending too-fast socket

        if selectors:
            self.sel = selectors.DefaultSelector()
        else:
            self.sel = None

    def add_conn_pair(self, conn1, conn2, callback=None):
        """
        transfer anything between two sockets

        :type conn1: socket.socket
        :type conn2: socket.socket
        :param callback: callback in connection finish
        :type callback: Callable
        """
        # change to non-blocking
        #   we use select or epoll to notice when data is ready
        conn1.setblocking(False)
        conn2.setblocking(False)

        # mark as readable+writable
        self.conn_rd.add(conn1)
        self.conn_wr.add(conn1)
        self.conn_rd.add(conn2)
        self.conn_wr.add(conn2)

        # record sockets pairs
        self.map[conn1] = conn2
        self.map[conn2] = conn1

        # record callback
        if callback is not None:
            self.callbacks[conn1] = callback

        if self.sel:
            self.sel.register(conn1, EVENT_READ_WRITE)
            self.sel.register(conn2, EVENT_READ_WRITE)

    def start_as_daemon(self):
        t = threading.Thread(target=self.start)
        t.daemon = True
        t.start()
        log.info("SocketBridge daemon started")
        return t

    def start(self):
        while True:
            try:
                self._start()
            except:
                log.error("FATAL ERROR! SocketBridge failed {}".format(
                    traceback.format_exc()
                ))

    def _start(self):

        while True:
            if not self.conn_rd and not self.conn_wr:
                # sleep if there is no connections
                time.sleep(0.01)
                continue

            # blocks until there is socket(s) ready for .recv
            # notice: sockets which were closed by remote,
            #   are also regarded as read-ready by select()
            if self.sel:
                events = self.sel.select(0.5)
                socks_rd = tuple(key.fileobj for key, mask in events if mask & EVENT_READ)
                socks_wr = tuple(key.fileobj for key, mask in events if mask & EVENT_WRITE)
            else:
                r, w, _ = select.select(self.conn_rd, self.conn_wr, [], 0.5)
                socks_rd = tuple(r)
                socks_wr = tuple(w)
                # log.debug('socks_rd: %s, socks_wr:%s', len(socks_rd), len(socks_wr))

            if not socks_rd and not self.send_buff:  # reduce CPU in low traffic
                time.sleep(0.005)
            # log.debug('got rd:%s wr:%s', socks_rd, socks_wr)

            # ----------------- RECEIVING ----------------
            # For prevent high CPU at slow network environment, we record if there is any
            #   success network operation, if we did nothing in single loop, we'll sleep a while.
            _stuck_network = True

            for s in socks_rd:  # type: socket.socket
                # if this socket has non-sent data, stop recving more, to prevent buff blowing up.
                if self.map[s] in self.send_buff:
                    # log.debug('delay recv because another too slow %s', self.map.get(s))
                    continue
                _stuck_network = False

                try:
                    received = s.recv(RECV_BUFFER_SIZE)
                    # log.debug('recved %s from %s', len(received), s)
                except Exception as e:

                    # unable to read, in most cases, it's due to socket close
                    log.warning('error reading socket %s, %s closing', repr(e), s)
                    self._rd_shutdown(s)
                    continue

                if not received:
                    self._rd_shutdown(s)
                    continue
                else:
                    self.send_buff[self.map[s]] = received

            # ----------------- SENDING ----------------
            for s in socks_wr:
                if s not in self.send_buff:
                    if self.map.get(s) not in self.conn_rd:
                        self._wr_shutdown(s)
                    continue
                _stuck_network = False

                data = self.send_buff.pop(s)
                try:
                    s.send(data)
                    # log.debug('sent %s to %s', len(data), s)
                except Exception as e:
                    # unable to send, close connection
                    log.warning('error sending socket %s, %s closing', repr(e), s)
                    self._wr_shutdown(s)
                    continue

            if _stuck_network:  # slower at bad network
                time.sleep(0.001)

    def _sel_disable_event(self, conn, ev):
        try:
            _key = self.sel.get_key(conn)  # type:selectors.SelectorKey
        except KeyError:
            pass
        else:
            if _key.events == EVENT_READ_WRITE:
                self.sel.modify(conn, EVENT_READ_WRITE ^ ev)
            else:
                self.sel.unregister(conn)

    def _rd_shutdown(self, conn, once=False):
        """action when connection should be read-shutdown
        :type conn: socket.socket
        """
        if conn in self.conn_rd:
            self.conn_rd.remove(conn)
            if self.sel:
                self._sel_disable_event(conn, EVENT_READ)

        # if conn in self.send_buff:
        #     del self.send_buff[conn]

        try:
            conn.shutdown(socket.SHUT_RD)
        except:
            pass

        if not once and conn in self.map:  # use the `once` param to avoid infinite loop
            # if a socket is rd_shutdowned, then it's
            #   pair should be wr_shutdown.
            self._wr_shutdown(self.map[conn], True)

        if self.map.get(conn) not in self.conn_rd:
            # if both two connection pair was rd-shutdowned,
            #   this pair sockets are regarded to be completed
            #   so we gonna close them
            self._terminate(conn)

    def _wr_shutdown(self, conn, once=False):
        """action when connection should be write-shutdown
        :type conn: socket.socket
        """
        try:
            conn.shutdown(socket.SHUT_WR)
        except:
            pass

        if conn in self.conn_wr:
            self.conn_wr.remove(conn)
            if self.sel:
                self._sel_disable_event(conn, EVENT_WRITE)

        if not once and conn in self.map:  # use the `once` param to avoid infinite loop
            #   pair should be rd_shutdown.
            # if a socket is wr_shutdowned, then it's
            self._rd_shutdown(self.map[conn], True)

    def _terminate(self, conn, once=False):
        """terminate a sockets pair (two socket)
        :type conn: socket.socket
        :param conn: any one of the sockets pair
        """
        try_close(conn)  # close the first socket

        # ------ close and clean the mapped socket, if exist ------
        _another_conn = self.map.pop(conn, None)

        self.send_buff.pop(conn, None)
        if self.sel:
            try:
                self.sel.unregister(conn)
            except:
                pass

        # ------ callback --------
        # because we are not sure which socket are assigned to callback,
        #   so we should try both
        if conn in self.callbacks:
            try:
                self.callbacks[conn]()
            except Exception as e:
                log.error("traceback error: {}".format(e))
                log.debug(traceback.format_exc())
            del self.callbacks[conn]

        # terminate another
        if not once and _another_conn in self.map:
            self._terminate(_another_conn)


class CtrlPkg(object):
    """
    Control Packages of Shootback, not completed yet
Currently, we have: handshake and heartbeat

NOTICE: If you are a non-Chinese reader,
please contact me for the following Chinese comment's translation
http://github.com/aploium

Control Package Structure, total length 64 bytes CtrlPkg.FORMAT_PKG
Using big-endian

Size   Name         Data Type          Description
1      pkg_ver      unsigned char      Package version  *1
1      pkg_type     signed char        Package type  *2
2      prgm_ver     unsigned short     Program version  *3
20     N/A          N/A                Reserved
40     data         bytes              Data area  *4

*1: Package version. The definition version of the package's overall structure, currently only 0x01.

*2: Package type. Except for heartbeat, all negative packages represent those sent by the Slaver, and positive packages
 are sent by the Master.
    -1: Handshake response package from Slaver to Master  PTYPE_HS_S2M
     0: Heartbeat package  PTYPE_HEART_BEAT
    +1: Handshake package from Master to Slaver  PTYPE_HS_M2S

*3: Default is INTERNAL_VERSION

*4: The contents in the data area are defined by the specific type of package itself.

-------------- Data Area Definitions ------------------
Package type: -1 (Handshake response package from Slaver to Master)
    Size   Name            Data Type         Description
     4    crc32_s2m       unsigned int     CRC32 for simple authentication (Reversed(SECRET_KEY))
     1    ssl_flag        unsigned char    Whether SSL is supported
     Others are empty
     *Note: For -1 handshake package, CRC32 is calculated by reversing the SECRET_KEY string, and for +1 handshake
     package, no pre-reversal is done.

Package type: 0 (Heartbeat)
   Data area is empty

Package type: +1 (Handshake package from Master to Slaver)
    Size   Name            Data Type         Description
     4    crc32_m2s       unsigned int     CRC32 for simple authentication (SECRET_KEY)
     1    ssl_flag        unsigned char    Whether SSL is supported
     Others are empty
    """
    PACKAGE_SIZE = 2 ** 6  # 64 bytes
    CTRL_PKG_TIMEOUT = 5  # CtrlPkg recv timeout, in second

    # CRC32 for SECRET_KEY and Reversed(SECRET_KEY)
    #   these values are set by `set_secretkey`
    SECRET_KEY_CRC32 = None  # binascii.crc32(SECRET_KEY.encode('utf-8')) & 0xffffffff
    SECRET_KEY_REVERSED_CRC32 = None  # binascii.crc32(SECRET_KEY[::-1].encode('utf-8')) & 0xffffffff

    # Package Type
    PTYPE_HS_S2M = -1  # handshake pkg, slaver to master
    PTYPE_HEART_BEAT = 0  # heart beat pkg
    PTYPE_HS_M2S = +1  # handshake pkg, Master to Slaver

    TYPE_NAME_MAP = {
        PTYPE_HS_S2M: "PTYPE_HS_S2M",
        PTYPE_HEART_BEAT: "PTYPE_HEART_BEAT",
        PTYPE_HS_M2S: "PTYPE_HS_M2S",
    }

    # formats
    # see https://docs.python.org/3/library/struct.html#format-characters
    #   for format syntax
    FORMAT_PKG = b"!b b H 20x 40s"
    FORMATS_DATA = {
        PTYPE_HS_S2M: b"!I B 35x",
        PTYPE_HEART_BEAT: b"!40x",
        PTYPE_HS_M2S: b"!I B 35x",
    }

    SSL_FLAG_NONE = 0
    SSL_FLAG_AVAIL = 1

    def __init__(self, pkg_ver=0x01, pkg_type=0,
                 prgm_ver=INTERNAL_VERSION, data=(),
                 raw=None,
                 ):
        """do not call this directly, use `CtrlPkg.pbuild_*` instead"""
        self.pkg_ver = pkg_ver
        self.pkg_type = pkg_type
        self.prgm_ver = prgm_ver
        self.data = data
        if raw:
            self.raw = raw
        else:
            self._build_bytes()

    @property
    def type_name(self):
        """返回人类可读的包类型"""
        return self.TYPE_NAME_MAP.get(self.pkg_type, "TypeUnknown")

    def __str__(self):
        return """pkg_ver: {} pkg_type:{} prgm_ver:{} data:{}""".format(
            self.pkg_ver,
            self.type_name,
            self.prgm_ver,
            self.data,
        )

    def __repr__(self):
        return self.__str__()

    def _build_bytes(self):
        self.raw = struct.pack(
            self.FORMAT_PKG,
            self.pkg_ver,
            self.pkg_type,
            self.prgm_ver,
            self.data_encode(self.pkg_type, self.data),
        )

    @classmethod
    def recalc_crc32(cls):
        cls.SECRET_KEY_CRC32 = binascii.crc32(SECRET_KEY.encode('utf-8')) & 0xffffffff
        cls.SECRET_KEY_REVERSED_CRC32 = binascii.crc32(SECRET_KEY[::-1].encode('utf-8')) & 0xffffffff

    @classmethod
    def data_decode(cls, ptype, data_raw):
        return struct.unpack(cls.FORMATS_DATA[ptype], data_raw)

    @classmethod
    def data_encode(cls, ptype, data):
        return struct.pack(cls.FORMATS_DATA[ptype], *data)

    def verify(self, pkg_type=None):
        try:
            if pkg_type is not None and self.pkg_type != pkg_type:
                return False
            elif self.pkg_type == self.PTYPE_HS_S2M:
                # Slaver-->Master 的握手响应包
                return self.data[0] == self.SECRET_KEY_REVERSED_CRC32

            elif self.pkg_type == self.PTYPE_HEART_BEAT:
                # 心跳
                return True

            elif self.pkg_type == self.PTYPE_HS_M2S:
                # Master-->Slaver 的握手包
                return self.data[0] == self.SECRET_KEY_CRC32

            else:
                return True
        except:
            return False

    @classmethod
    def decode_only(cls, raw):
        """
        decode raw bytes to CtrlPkg instance, no verify
        use .decode_verify() if you also want verify

        :param raw: raw bytes content of package
        :type raw: bytes
        :rtype: CtrlPkg
        """
        if not raw or len(raw) != cls.PACKAGE_SIZE:
            raise ValueError("content size should be {}, but {}".format(
                cls.PACKAGE_SIZE, len(raw)
            ))
        pkg_ver, pkg_type, prgm_ver, data_raw = struct.unpack(cls.FORMAT_PKG, raw)
        data = cls.data_decode(pkg_type, data_raw)

        return cls(
            pkg_ver=pkg_ver, pkg_type=pkg_type,
            prgm_ver=prgm_ver,
            data=data,
            raw=raw,
        )

    @classmethod
    def decode_verify(cls, raw, pkg_type=None):
        """decode and verify a package
        :param raw: raw bytes content of package
        :type raw: bytes
        :param pkg_type: assert this package's type,
            if type not match, would be marked as wrong
        :type pkg_type: int

        :rtype: CtrlPkg, bool
        :return: tuple(CtrlPkg, is_it_a_valid_package)
        """
        try:
            pkg = cls.decode_only(raw)
        except Exception as e:
            log.error('unable to decode package. raw: %s', raw, exc_info=True)
            return None, False
        else:
            return pkg, pkg.verify(pkg_type=pkg_type)

    @classmethod
    def pbuild_hs_m2s(cls, ssl_avail=False):
        """pkg build: Handshake Master to Slaver
        """
        ssl_flag = cls.SSL_FLAG_AVAIL if ssl_avail else cls.SSL_FLAG_NONE
        return cls(
            pkg_type=cls.PTYPE_HS_M2S,
            data=(cls.SECRET_KEY_CRC32, ssl_flag),
        )

    @classmethod
    def pbuild_hs_s2m(cls, ssl_avail=False):
        """pkg build: Handshake Slaver to Master"""
        ssl_flag = cls.SSL_FLAG_AVAIL if ssl_avail else cls.SSL_FLAG_NONE
        return cls(
            pkg_type=cls.PTYPE_HS_S2M,
            data=(cls.SECRET_KEY_REVERSED_CRC32, ssl_flag),
        )

    @classmethod
    def pbuild_heart_beat(cls):
        """pkg build: Heart Beat Package"""
        return cls(
            pkg_type=cls.PTYPE_HEART_BEAT,
        )

    @classmethod
    def recv(cls, sock, timeout=CTRL_PKG_TIMEOUT, expect_ptype=None):
        """just a shortcut function
        :param sock: which socket to recv CtrlPkg from
        :type sock: socket.socket
        :rtype: CtrlPkg,bool
        """
        buff = select_recv(sock, cls.PACKAGE_SIZE, timeout)
        pkg, verify = CtrlPkg.decode_verify(buff, pkg_type=expect_ptype)  # type: CtrlPkg,bool
        return pkg, verify
