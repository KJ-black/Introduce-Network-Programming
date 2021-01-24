# version=2020/11/19
import sys # to use the argv
import socket 
import select
import queue
import tty
import termios
close_recv = "close" # to close the unuse recv

class NonBlockingConsole(object):
    
    def __enter__(self):
        self.old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno()) # sys.stdin.fileno() == 0 ( stdout == 1, stderr == 2)
        return self

    def __exit__(self, type, value, traceback):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)


    def get_data(self):
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            return sys.stdin.read(1)
        return False

if __name__ == "__main__":
    ## the host and service
    if len(sys.argv) != 3:
        sys.exit("iter_tcp_client.py {host} {portnumber}")
    else:
        port = int(sys.argv[2])
        host = sys.argv[1]
    addr = (host, port)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(addr)
    s.setblocking(0)	
    s.settimeout(0.01)

    # recv welcome
    wel = str(s.recv(1024), encoding='utf-8')
    print(wel)

    msgs = ""
    with NonBlockingConsole() as nbc:
        while True:
            try:
                data = str(s.recv(1024), encoding='utf-8')
                print(data)
            except:
                pass
            msg = nbc.get_data() # to get the console input nonblockingly
            if msg and ord(msg)==10:
                # print("ENTER")
                if msgs == "exit":
                    print(msgs)
                    s.sendall(msgs.encode())
                    break
                else:
                    print(msgs)
                    if "mute"  == msgs or "unmute" == msgs or  "yell" in msgs or "tell" in msgs:
                        s.sendall(msgs.encode())
                    msgs=""
            elif msg:
                msgs += msg
    s.close()