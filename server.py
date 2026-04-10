import socket
import threading
import os
from datetime import datetime

HOST="0.0.0.0"
PORT=5000

users=set()

if not os.path.exists("mailboxes"):
    os.mkdir("mailboxes")

# LOG FUNCTION
def log(msg,level="INFO"):
    with open("server_log.txt","a") as f:
        f.write(f"[{level}] {datetime.now()} : {msg}\n")

# SAVE MAIL
def save_mail(sender,rec,sub,msg):
    try:
        path=f"mailboxes/{rec}.txt"
        mail_id=1

        if os.path.exists(path):
            with open(path) as f:
                mail_id=f.read().count("ID:")+1

        with open(path,"a") as f:
            f.write(f"ID:{mail_id}\nFROM:{sender}\nSUBJECT:{sub}\nMESSAGE:{msg.strip()}\n\n")

        return True
    except Exception as e:
        log(f"Mail save failed ({sender}->{rec}) : {str(e)}","ERROR")
        return False

# CLIENT HANDLER
def handle(conn):
    user=None

    while True:
        try:
            data=conn.recv(4096).decode()
            if not data:
                break

            cmd=data.split()

            # LOGIN / REGISTER
            if cmd[0]=="LOGIN":
                user=cmd[1]

                if user not in users:
                    users.add(user)
                    log(f"{user} registered")

                conn.send("OK".encode())
                log(f"{user} logged in")

            # SEND MAIL
            elif cmd[0]=="SEND":
                rec=cmd[1]

                if user is None:
                    conn.send("ERR:Login first".encode())
                    log("Send attempt without login","ERROR")
                    continue

                if rec not in users:
                    conn.send("ERR:User does not exist".encode())
                    log(f"{user} tried sending to invalid user {rec}","ERROR")
                    continue

                conn.send("SUB".encode())
                sub=conn.recv(1024).decode()

                conn.send("MSG".encode())
                msg=conn.recv(4096).decode()

                success=save_mail(user,rec,sub,msg)

                if success:
                    conn.send("SENT".encode())
                    log(f"{user} -> {rec} (SUCCESS)")
                else:
                    conn.send("ERR:Delivery failed".encode())
                    log(f"{user} -> {rec} (FAILED)","ERROR")

            # LIST MAILS
            elif cmd[0]=="LIST":
                if user is None:
                    conn.send("ERR:Login first".encode())
                    log("List attempted without login","ERROR")
                    continue

                path=f"mailboxes/{user}.txt"

                if not os.path.exists(path):
                    conn.send("EMPTY:No mails found".encode())
                    log(f"{user} checked empty mailbox")
                    continue

                with open(path,"r") as f:
                    data=f.read()

                conn.send(data.encode())
                log(f"{user} viewed mailbox")

            # CONTACTS
            elif cmd[0]=="CONTACTS":
                if len(users)==0:
                    conn.send("EMPTY:No users".encode())
                else:
                    conn.send(",".join(users).encode())

            elif cmd[0]=="QUIT":
                log(f"{user} disconnected")
                break

        except Exception as e:
            log(f"Server error: {str(e)}","ERROR")
            break

    conn.close()

# START SERVER
server=socket.socket()
server.bind((HOST,PORT))
server.listen()

print("Email Server Running...")

while True:
    c,a=server.accept()
    log(f"Connection from {a}")
    threading.Thread(target=handle,args=(c,)).start()
