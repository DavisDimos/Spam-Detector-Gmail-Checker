# Spam_gui.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix, classification_report
import warnings
import threading
warnings.filterwarnings('ignore')

# Εισαγωγή των συναρτήσεων από το Spam.py
from Spam import predict_spam, clean_text, tfidf, nb_classifier, le, df

class RightClickMenu:
    """Κλάση για το μενού δεξιού κλικ"""
    
    def __init__(self, widget):
        self.widget = widget
        self.menu = tk.Menu(widget, tearoff=0)
        self.create_menu()
        self.bind_events()
    
    def create_menu(self):
        """Δημιουργία των επιλογών του μενού"""
        self.menu.add_command(label="Αντιγραφή", command=self.copy_text)
        self.menu.add_command(label="Απόκοψη", command=self.cut_text)
        self.menu.add_command(label="Επικόλληση", command=self.paste_text)
        self.menu.add_separator()
        self.menu.add_command(label="Επιλογή Όλου", command=self.select_all)
    
    def bind_events(self):
        """Σύνδεση events για δεξί κλικ"""
        self.widget.bind("<Button-3>", self.show_menu)  # Button-3 = δεξί κλικ
        self.widget.bind("<Control-a>", self.select_all)  # Ctrl+A για επιλογή όλου
        self.widget.bind("<Control-c>", lambda e: self.copy_text())  # Ctrl+C
        self.widget.bind("<Control-x>", lambda e: self.cut_text())   # Ctrl+X
        self.widget.bind("<Control-v>", lambda e: self.paste_text()) # Ctrl+V
    
    def show_menu(self, event):
        """Εμφάνιση του μενού στη θέση του ποντικιού"""
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()
    
    def copy_text(self):
        """Αντιγραφή επιλεγμένου κειμένου"""
        try:
            # Για ScrolledText widgets
            if hasattr(self.widget, 'get'):
                selected_text = self.widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.widget.clipboard_clear()
                self.widget.clipboard_append(selected_text)
        except tk.TclError:
            # Δεν έχει επιλεγεί κείμενο
            pass
    
    def cut_text(self):
        """Απόκοψη επιλεγμένου κειμένου"""
        try:
            # Για ScrolledText widgets
            if hasattr(self.widget, 'get'):
                selected_text = self.widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.widget.clipboard_clear()
                self.widget.clipboard_append(selected_text)
                self.widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            # Δεν έχει επιλεγεί κείμενο
            pass
    
    def paste_text(self):
        """Επικόλληση κειμένου από clipboard"""
        try:
            clipboard_text = self.widget.clipboard_get()
            if hasattr(self.widget, 'insert'):
                if self.widget.tag_ranges(tk.SEL):
                    # Αντικατάσταση επιλεγμένου κειμένου
                    self.widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                self.widget.insert(tk.INSERT, clipboard_text)
        except tk.TclError:
            # Το clipboard είναι άδειο
            pass
        except Exception as e:
            print(f"Σφάλμα επικόλλησης: {e}")
    
    def select_all(self, event=None):
        """Επιλογή όλου του κειμένου"""
        try:
            if hasattr(self.widget, 'tag_add'):
                self.widget.tag_add(tk.SEL, "1.0", tk.END)
                self.widget.mark_set(tk.INSERT, "1.0")
                self.widget.see(tk.INSERT)
            return "break"  # Αποτρέπει την προεπιλεγμένη συμπεριφορά
        except Exception as e:
            print(f"Σφάλμα επιλογής όλου: {e}")

class SpamDetectorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📧 Spam Detector - User Interface")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Ιστορικό προβλέψεων
        self.predictions_history = []
        
        self.setup_ui()
        
    def setup_ui(self):
        # Κύρια ομάδα widgets
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Τίτλος
        title_label = ttk.Label(main_frame, text="🔍 Spam Message Detector", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Περιοχή εισαγωγής μηνύματος
        input_frame = ttk.LabelFrame(main_frame, text="Εισαγωγή Μηνύματος", padding="10")
        input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(input_frame, text="Εισάγετε το μήνυμα για έλεγχο:").grid(row=0, column=0, sticky=tk.W)
        
        self.message_text = scrolledtext.ScrolledText(input_frame, width=70, height=6, font=('Arial', 10))
        self.message_text.grid(row=1, column=0, columnspan=2, pady=(5, 10), sticky=(tk.W, tk.E))
        
        # Κουμπιά ενεργειών
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="🔍 Έλεγχος Μηνύματος", 
                  command=self.check_message).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="🧹 Καθαρισμός", 
                  command=self.clear_text).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="📊 Εμφάνιση Γραφικών", 
                  command=self.show_analytics).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="📧 Έλεγχος Gmail", 
                  command=self.open_gmail_checker).pack(side=tk.LEFT)
        
        # Περιοχή αποτελεσμάτων
        results_frame = ttk.LabelFrame(main_frame, text="Αποτελέσματα", padding="10")
        results_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.result_text = scrolledtext.ScrolledText(results_frame, width=70, height=8, font=('Arial', 10))
        self.result_text.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Ιστορικό προβλέψεων
        history_frame = ttk.LabelFrame(main_frame, text="Ιστορικό Προβλέψεων", padding="10")
        history_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.history_text = scrolledtext.ScrolledText(history_frame, width=70, height=6, font=('Arial', 9))
        self.history_text.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Προσθήκη μενού δεξιού κλικ ΜΟΝΟ στο αρχικό text area
        self.setup_right_click_menu()
        
        # Ρύθμιση weights για responsive design
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        input_frame.columnconfigure(0, weight=1)
        results_frame.columnconfigure(0, weight=1)
        history_frame.columnconfigure(0, weight=1)
    
    def setup_right_click_menu(self):
        """Προσθήκη μενού δεξιού κλικ ΜΟΝΟ στο αρχικό text area"""
        self.message_menu = RightClickMenu(self.message_text)
    
    def check_message(self):
        """Έλεγχος του μηνύματος για spam"""
        message = self.message_text.get("1.0", tk.END).strip()
        
        if not message:
            messagebox.showwarning("Προειδοποίηση", "Παρακαλώ εισάγετε ένα μήνυμα για έλεγχο.")
            return
        
        try:
            # Χρήση της predict_spam από το Spam.py
            result = predict_spam(message)
            
            # Λήψη πιθανότητας
            cleaned_msg = clean_text(message)
            msg_vector = tfidf.transform([cleaned_msg]).toarray()
            probability = nb_classifier.predict_proba(msg_vector)[0]
            confidence = max(probability)
            
            # Προσδιορισμός κατηγορίας
            prediction_class = le.classes_[np.argmax(probability)]
            
            # Εμφάνιση αποτελεσμάτων
            result_str = f"📨 Μήνυμα: {message}\n"
            result_str += f"🔍 Αποτέλεσμα: {prediction_class}\n"
            result_str += f"📊 Βεβαιότητα: {confidence:.4f}\n"
            result_str += f"📈 Πιθανότητες: [ham: {probability[0]:.4f}, spam: {probability[1]:.4f}]\n"
            result_str += "─" * 50 + "\n"
            
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", result_str)
            
            # Αποθήκευση στο ιστορικό
            self.predictions_history.append({
                'message': message[:100] + "..." if len(message) > 100 else message,
                'prediction': prediction_class,
                'confidence': confidence,
                'probabilities': probability
            })
            
            # Ενημέρωση ιστορικού
            self.update_history()
            
        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Προέκυψε σφάλμα κατά τον έλεγχο: {str(e)}")
    
    def clear_text(self):
        """Καθαρισμός των περιοχών κειμένου"""
        self.message_text.delete("1.0", tk.END)
        self.result_text.delete("1.0", tk.END)
    
    def update_history(self):
        """Ενημέρωση του ιστορικού προβλέψεων"""
        self.history_text.delete("1.0", tk.END)
        
        if not self.predictions_history:
            self.history_text.insert("1.0", "Δεν υπάρχουν προηγούμενες προβλέψεις.")
            return
        
        for i, pred in enumerate(reversed(self.predictions_history[-10:]), 1):
            history_entry = f"{i}. {pred['prediction']} ({pred['confidence']:.3f}): {pred['message']}\n"
            self.history_text.insert("1.0", history_entry)
    
    def show_analytics(self):
        """Εμφάνιση γραφικών και στατιστικών"""
        try:
            # Δημιουργία νέου παραθύρου για τα γραφικά
            analytics_window = tk.Toplevel(self.root)
            analytics_window.title("📊 Αναλυτικά Γραφικά")
            analytics_window.geometry("900x700")
            
            # Notebook για πολλαπλές καρτέλες
            notebook = ttk.Notebook(analytics_window)
            
            # Κατανομή δεδομένων
            dist_frame = ttk.Frame(notebook)
            notebook.add(dist_frame, text="Κατανομή Δεδομένων")
            
            # Συνολικές στατιστικές
            stats_frame = ttk.Frame(notebook)
            notebook.add(stats_frame, text="Στατιστικά")
            
            # Προβλέψεις χρήστη
            user_frame = ttk.Frame(notebook)
            notebook.add(user_frame, text="Προβλέψεις Χρήστη")
            
            notebook.pack(expand=True, fill='both', padx=10, pady=10)
            
            # Γράφημα 1: Κατανομή labels στο dataset
            self.create_distribution_plot(dist_frame)
            
            # Γράφημα 2: Στατιστικά μοντέλου
            self.create_model_stats(stats_frame)
            
            # Γράφημα 3: Ιστορικό προβλέψεων χρήστη
            self.create_user_predictions_plot(user_frame)
            
        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Προέκυψε σφάλμα κατά τη δημιουργία γραφικών: {str(e)}")
    
    def open_gmail_checker(self):
        """Άνοιγμα του Gmail Checker"""
        try:
            from gmail_checker import GmailChecker
            gmail_window = tk.Toplevel(self.root)
            gmail_app = GmailChecker(gmail_window)
        except ImportError as e:
            messagebox.showerror("Σφάλμα", f"Δεν βρέθηκε το αρχείο gmail_checker.py: {e}")
        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Προέκυψε σφάλμα: {e}")
    
    def create_distribution_plot(self, parent):
        """Δημιουργία γραφήματος κατανομής δεδομένων"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Κατανομή labels
        label_counts = df['label'].value_counts()
        colors = ['#66b3ff', '#ff6666']
        
        ax1.pie(label_counts.values, labels=label_counts.index, autopct='%1.1f%%', 
                colors=colors, startangle=90)
        ax1.set_title('Κατανομή Μηνυμάτων (Ham vs Spam)')
        
        # Μήκος μηνυμάτων
        df['message_length'] = df['message'].str.len()
        df.boxplot(column='message_length', by='label', ax=ax2)
        ax2.set_title('Μήκος Μηνυμάτων ανά Κατηγορία')
        ax2.set_ylabel('Μήκος Χαρακτήρων')
        
        plt.suptitle('')
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_model_stats(self, parent):
        """Δημιουργία στατιστικών μοντέλου"""
        from Spam import X_test, y_test, nb_classifier
        
        # Πρόβλεψη στο test set
        y_pred = nb_classifier.predict(X_test)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=le.classes_, yticklabels=le.classes_, ax=ax1)
        ax1.set_xlabel('Predicted')
        ax1.set_ylabel('Actual')
        ax1.set_title('Confusion Matrix')
        
        # Classification Report (απλοποιημένο)
        report = classification_report(y_test, y_pred, target_names=le.classes_, output_dict=True)
        metrics_df = pd.DataFrame(report).transpose()
        
        # Γράφημα accuracy
        categories = ['Precision', 'Recall', 'F1-Score']
        ham_scores = [report['ham'][cat.lower()] for cat in categories]
        spam_scores = [report['spam'][cat.lower()] for cat in categories]
        
        x = np.arange(len(categories))
        width = 0.35
        
        ax2.bar(x - width/2, ham_scores, width, label='Ham', color='#66b3ff')
        ax2.bar(x + width/2, spam_scores, width, label='Spam', color='#ff6666')
        
        ax2.set_xlabel('Μετρικές')
        ax2.set_ylabel('Score')
        ax2.set_title('Μετρικές Αξιολόγησης ανά Κατηγορία')
        ax2.set_xticks(x)
        ax2.set_xticklabels(categories)
        ax2.legend()
        ax2.set_ylim(0, 1)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_user_predictions_plot(self, parent):
        """Δημιουργία γραφήματος για τις προβλέψεις του χρήστη"""
        if not self.predictions_history:
            label = ttk.Label(parent, text="Δεν υπάρχουν προβλέψεις για εμφάνιση.", 
                             font=('Arial', 12))
            label.pack(expand=True)
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Κατανομή προβλέψεων χρήστη
        user_preds = [pred['prediction'] for pred in self.predictions_history]
        pred_counts = pd.Series(user_preds).value_counts()
        
        ax1.pie(pred_counts.values, labels=pred_counts.index, autopct='%1.1f%%', 
                colors=['#66b3ff', '#ff6666'], startangle=90)
        ax1.set_title('Κατανομή Προβλέψεων Χρήστη')
        
        # Βεβαιότητα προβλέψεων
        confidences = [pred['confidence'] for pred in self.predictions_history]
        ax2.hist(confidences, bins=10, alpha=0.7, color='skyblue', edgecolor='black')
        ax2.set_xlabel('Βεβαιότητα')
        ax2.set_ylabel('Συχνότητα')
        ax2.set_title('Κατανομή Βεβαιότητας Προβλέψεων')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def main():
    """Κύρια συνάρτηση"""
    root = tk.Tk()
    app = SpamDetectorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()