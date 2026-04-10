import socket
import tkinter as tk
from tkinter import messagebox

HOST="127.0.0.1"
PORT=5000

client=socket.socket()
client.connect((HOST,PORT))

root=tk.Tk()
root.title("Mail Client")
root.geometry("900x550")
root.configure(bg="#f4f6f9")

username=tk.StringVar()

# TOP BAR
top=tk.Frame(root,bg="#2f3542",height=50)
top.pack(fill="x")

tk.Label(top,text="Simple Mail",fg="white",bg="#2f3542",
         font=("Segoe UI",14,"bold")).pack(side="left",padx=10)

user_label=tk.Label(top,text="",fg="white",bg="#2f3542",
                    font=("Segoe UI",10))
user_label.pack(side="right",padx=10)

# ACCOUNT POPUP
def open_account():
    win=tk.Toplevel(root)
    win.title("Account")
    win.geometry("300x150")

    tk.Label(win,text="Enter Username").pack(pady=10)

    entry=tk.Entry(win,textvariable=username)
    entry.pack(pady=5)

    def submit():
        client.send(f"LOGIN {username.get()}".encode())
        res=client.recv(1024).decode()

        if res=="OK":
            user_label.config(text=username.get())
            messagebox.showinfo("Welcome",f"Logged in as {username.get()}")
            win.destroy()
            refresh()

    tk.Button(win,text="Continue",command=submit,
              bg="#1e90ff",fg="white").pack(pady=10)

tk.Button(top,text="Account",command=open_account,
          bg="#ffa502",fg="white").pack(side="right",padx=10)

# MAIN LAYOUT
main=tk.Frame(root,bg="#dfe4ea")
main.pack(fill="both",expand=True)

sidebar=tk.Frame(main,bg="#57606f",width=150)
sidebar.pack(side="left",fill="y")

inbox_frame=tk.Frame(main,bg="white",width=250)
inbox_frame.pack(side="left",fill="y")

read_frame=tk.Frame(main,bg="white")
read_frame.pack(side="right",fill="both",expand=True)

tk.Label(inbox_frame,text="Inbox",
         font=("Segoe UI",12,"bold")).pack(anchor="w",padx=10,pady=5)

mail_list=tk.Listbox(inbox_frame,font=("Segoe UI",10))
mail_list.pack(fill="both",expand=True,padx=10,pady=5)

mail_view=tk.Text(read_frame,font=("Segoe UI",10))
mail_view.pack(fill="both",expand=True,padx=10,pady=10)

emails=[]

# REFRESH (FIXED PARSING)
def refresh():
    client.send("LIST".encode())
    res=client.recv(4096).decode()

    mail_list.delete(0,tk.END)
    mail_view.delete("1.0",tk.END)
    emails.clear()

    if res.startswith("EMPTY"):
        messagebox.showinfo("Inbox",res)
        return

    if res.startswith("ERR"):
        messagebox.showerror("Error",res)
        return

    mails=res.strip().split("\n\n")

    for mail in mails:
        lines=mail.strip().split("\n")

        sender="Unknown"

        for line in lines:
            if line.startswith("FROM:"):
                sender=line.replace("FROM:","")
                break

        mail_list.insert(tk.END,sender)
        emails.append(mail)

# SHOW MAIL (ROBUST)
def show(evt):
    sel=mail_list.curselection()
    if not sel:
        return

    mail_view.delete("1.0",tk.END)

    lines=emails[sel[0]].split("\n")

    sender=""
    subject=""
    body=""

    for line in lines:
        if line.startswith("FROM:"):
            sender=line.replace("FROM:","")
        elif line.startswith("SUBJECT:"):
            subject=line.replace("SUBJECT:","")
        elif line.startswith("MESSAGE:"):
            body=line.replace("MESSAGE:","")
        else:
            body += "\n"+line

    mail_view.tag_config("bold",font=("Segoe UI",11,"bold"))

    mail_view.insert(tk.END,f"From: {sender}\n","bold")
    mail_view.insert(tk.END,f"{subject}\n","bold")
    mail_view.insert(tk.END,"-"*60+"\n")
    mail_view.insert(tk.END,body.strip())

mail_list.bind("<<ListboxSelect>>",show)

# CONTACTS
def show_contacts():
    client.send("CONTACTS".encode())
    res=client.recv(1024).decode()

    if res=="EMPTY":
        messagebox.showinfo("Contacts","No users found")
        return

    win=tk.Toplevel(root)
    win.title("Contacts")
    win.geometry("250x300")

    tk.Label(win,text="All Users",
             font=("Segoe UI",12,"bold")).pack(pady=10)

    lst=tk.Listbox(win)
    lst.pack(fill="both",expand=True,padx=10,pady=5)

    for u in res.split(","):
        lst.insert(tk.END,u)

# COMPOSE
def compose():
    win=tk.Toplevel(root)
    win.title("Compose Mail")
    win.geometry("500x420")

    rec=tk.StringVar()
    sub=tk.StringVar()

    tk.Label(win,text="To").pack(anchor="w",padx=10,pady=5)
    tk.Entry(win,textvariable=rec).pack(fill="x",padx=10)

    tk.Label(win,text="Subject").pack(anchor="w",padx=10,pady=5)
    tk.Entry(win,textvariable=sub,
             font=("Segoe UI",10)).pack(fill="x",padx=10,ipady=3)

    tk.Label(win,text="Message").pack(anchor="w",padx=10,pady=5)

    msg=tk.Text(win,height=12)
    msg.pack(fill="both",expand=True,padx=10)

    def send():
        client.send(f"SEND {rec.get()}".encode())
        r=client.recv(1024).decode()

        if r.startswith("ERR"):
            messagebox.showerror("Error",r)
            return

        if r=="SUB":
            client.send(sub.get().encode())

        r=client.recv(1024).decode()

        if r=="MSG":
            client.send(msg.get("1.0",tk.END).encode())

        r=client.recv(1024).decode()

        if r=="SENT":
            messagebox.showinfo("Mail","Sent successfully")
            win.destroy()
            refresh()

    tk.Button(win,text="Send",
              bg="#1e90ff",fg="white",
              command=send).pack(pady=10)

# SIDEBAR
tk.Button(sidebar,text="Compose",width=15,
          command=compose,bg="#2ed573",fg="white").pack(pady=20)

tk.Button(sidebar,text="Refresh",width=15,
          command=refresh,bg="#1e90ff",fg="white").pack()

tk.Button(sidebar,text="Contacts",width=15,
          command=show_contacts,bg="#ffa502",fg="white").pack(pady=10)

root.mainloop()
