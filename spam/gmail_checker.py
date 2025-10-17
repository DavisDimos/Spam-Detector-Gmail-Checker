import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import imaplib
import email
import time
import re
import string
import threading
from email.header import decode_header

# Εισαγωγή από το Spam
from Spam import predict_spam, clean_text

class GmailChecker:
    def __init__(self, root):
        self.root = root
        self.root.title("📧 Gmail Spam Checker")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        self.is_checking = False
        self.checking_thread = None
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        title_label = ttk.Label(main_frame, text="🔍 Gmail Spam Checker", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        settings_frame = ttk.LabelFrame(main_frame, text="Ρυθμίσεις Gmail", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(settings_frame, text="Gmail Username:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.username_entry = ttk.Entry(settings_frame, width=40, font=('Arial', 10))
        self.username_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5), padx=(10, 0))
        
        ttk.Label(settings_frame, text="App Password:").grid(row=1, column=0, sticky=tk.W, pady=(5, 5))
        self.password_entry = ttk.Entry(settings_frame, width=40, show="*", font=('Arial', 10))
        self.password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(5, 5), padx=(10, 0))
        
        info_label = ttk.Label(settings_frame, 
                              text="💡 Για App Password: Gmail Settings → Security → 2FA → App Passwords",
                              font=('Arial', 8), foreground='blue')
        info_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        control_frame = ttk.Frame(settings_frame)
        control_frame.grid(row=3, column=0, columnspan=2, pady=(15, 5))
        
        self.start_button = ttk.Button(control_frame, text="▶️ Έναρξη Ελέγχου", 
                                      command=self.start_checking)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="⏹️ Διακοπή", 
                                     command=self.stop_checking, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
        
        results_frame = ttk.LabelFrame(main_frame, text="Αποτελέσματα Ελέγχου", padding="10")
        results_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        self.results_text = scrolledtext.ScrolledText(results_frame, width=70, height=20, 
                                                     font=('Arial', 9))
        self.results_text.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="🔴 Σε αδράνεια", 
                                     font=('Arial', 10, 'bold'))
        self.status_label.pack(side=tk.LEFT)
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        settings_frame.columnconfigure(1, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
    
    def start_checking(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("Προειδοποίηση", "Παρακαλώ συμπληρώστε και τα δύο πεδία.")
            return
        
        self.is_checking = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="🟢 Ελέγχει Gmail...", foreground="green")
        
        self.results_text.delete("1.0", tk.END)
        self.log_message("🚀 Έναρξη ελέγχου Gmail...")
        
        self.checking_thread = threading.Thread(target=self.check_gmail, 
                                              args=(username, password), 
                                              daemon=True)
        self.checking_thread.start()
    
    def stop_checking(self):
        self.is_checking = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="🔴 Διακόπηκε", foreground="red")
        self.log_message("⏹️ Διακοπή ελέγχου...")
    
    def check_gmail(self, username, password):
        while self.is_checking:
            try:
                self.log_message("🔍 Σύνδεση στο Gmail...")
                
                # Σύνδεση στο Gmail
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(username, password)
                mail.select("inbox")
                
                
                status, messages = mail.search(None, "UNSEEN")
                
                if status == "OK":
                    email_ids = messages[0].split()
                    
                    if email_ids:
                        self.log_message(f"📫 Βρέθηκαν {len(email_ids)} νέα μηνύματα")
                    
                    for email_id in email_ids:
                        if not self.is_checking:
                            break
                            
                        status, msg_data = mail.fetch(email_id, "(RFC822)")
                        email_body = msg_data[0][1]
                        msg = email.message_from_bytes(email_body)
                        
                        subject = ""
                        if msg["Subject"]:
                            subject_data = decode_header(msg["Subject"])[0]
                            if isinstance(subject_data[0], bytes):
                                subject = subject_data[0].decode('utf-8')
                            else:
                                subject = str(subject_data[0])
                        
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    try:
                                        body = part.get_payload(decode=True).decode('utf-8')
                                        break
                                    except:
                                        continue
                        else:
                            try:
                                body = msg.get_payload(decode=True).decode('utf-8')
                            except:
                                body = ""
                        
                        full_message = f"{subject} {body}"
                        is_spam = self.check_if_spam_ml(full_message)
                        
                        result_text = f"\n📧 Νέο μήνυμα από: {msg['From']}\n"
                        result_text += f"📝 Θέμα: {subject}\n"
                        result_text += f"🚨 Αποτέλεσμα: {'SPAM' if is_spam else 'ΚΑΝΟΝΙΚΟ'}\n"
                        result_text += "-" * 50 + "\n"
                        
                        self.log_message(result_text)
                
                mail.close()
                mail.logout()
                
            except imaplib.IMAP4.error as e:
                self.log_message(f"❌ Σφάλμα σύνδεσης: Ελέγξτε τα credentials")
                self.stop_checking()
                break
            except Exception as e:
                self.log_message(f"❌ Σφάλμα: {e}")
            
            if self.is_checking:
                for i in range(30):
                    if not self.is_checking:
                        break
                    time.sleep(1)
    
    def check_if_spam_ml(self, message):
        try:
            result = predict_spam(message)
            return result.lower() == 'spam'
        except Exception as e:
            self.log_message(f"⚠️ Σφάλμα ML μοντέλου: {e}")
            # Εφεδρικός απλός έλεγχος
            return self.check_if_spam_basic(message)
    
    def check_if_spam_basic(self, message):
        spam_keywords = [
            'win', 'winner', 'prize', 'free', 'congratulations', 
            'cash', 'money', 'urgent', 'limited', 'offer',
            'discount', 'claim', 'call now', 'text yes'
        ]
        
        message_lower = message.lower()
        spam_count = sum(1 for keyword in spam_keywords if keyword in message_lower)
        
        return spam_count >= 2
    
    def log_message(self, message):
        def update_text():
            self.results_text.insert(tk.END, message + "\n")
            self.results_text.see(tk.END)
            self.results_text.update()
        
        self.root.after(0, update_text)

def main():
    root = tk.Tk()
    app = GmailChecker(root)
    root.mainloop()

if __name__ == "__main__":
    main()