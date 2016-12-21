from tkinter import *
from tkinter import ttk
import time
from tkinter import messagebox
import datetime
import os
FONT = "Arial"

class SavingGoal(object):
    """
    A class to store individual values for each goal pool
    This stores a current fund value and a list of transaction details
    in the form (amount, date, description)
    """
    def __init__(self, name,funds=0, transactions=[], increment=0):
        self._currentFunds = funds
        self._transactions = transactions
        self._increment = increment
        self._name=name

    def modify(self, amount, date, description = "Pay"):
        """
        Modifys the pool by a given amount and adds to the transaction list
        Throws an InsufficientFunds error if the transaction would leave < $0
        """
        if self._currentFunds + amount < 0:
            raise InsufficientFunds()
        self._currentFunds += amount
        self._transactions.append((amount, date, description))

    def get_amount(self):
        return self._currentFunds

    def get_transactions(self):
        return self._transactions

    def get_increment(self):
        return self._increment

    def get_name(self):
        return self._name

    def set_increment(self, amount):
        self._increment = amount

    def set_name(self, name):
        self._name=name

    def increment(self):
        self.modify(self._increment, time.strftime("%d/%m/%Y"))

class Goals(object):
    """
    A class to store all savings goals in one dictionary under a given name
    """
    def __init__(self):
        self._goals = [SavingGoal("Unallocated")]
        self._profile = ""
        self._config = {}
        self.load_config()

    def get_config(self):
        return self._config

    def set_config(self,config):
        self._config = config
        self.save_config()

    def get_profiles(self):
        profs = open("profiles.list",'r')
        profiles = []
        for line in profs:
            line = line.strip()
            if not line:
                continue
            profiles.append(line)
        profs.close()
        return profiles
        

    def save_config(self):
        fout = open("config.ini",'w')
        for setting in self._config.keys():
            fout.write("{0}={1}\n".format(setting,self._config[setting]))
        fout.close()

    def load_config(self):
        config_file=open("config.ini",'r')
        for line in config_file:
            line=line.strip()
            if not line or line.startswith("#"):
                continue
            split = line.split("=")
            self._config[split[0]] = split[1]
        config_file.close()

    def get_name(self):
        return self._profile
        
    def get_goals(self):
        return self._goals

    def get_goal(self, name):
        for goals in self._goals:
            if goals.get_name() == name:
                return goals
        return None

    def get_index(self,index):
        return self._goals[index]

    def get_total(self):
        total = 0
        for goals in self._goals:
            total+=goals.get_amount()
        return total

    def save(self):
        """
        Rewritten to save as single file
        """
        self.save_config()
        output=""
        for goal in self._goals:
            output += "{0},{1},{2}\n".format(goal.get_name(),goal.get_amount(), goal.get_increment())
            for amount,date,desc in goal.get_transactions():
                output += "{0},{1},{2}\n".format(amount,date,desc)
            output+="\n\n"
        fw = open("profile_{0}.save".format(self._profile),'w')
        fw.write(output)
        fw.close()

    def new_profile(self, name):
        self._goals = [SavingGoal("Unallocated")]
        self._profile = name

    def load(self, profile):
        """
        Rewritten to load new filetype and config
        """
        emp_line = False
        new_section = True
        self._profile=profile
        self._goals=[]
        first=True
        if profile=="":
            return
        else:
            prof = open("profile_{0}.save".format(profile),'r')
            trans = []
            for line in prof:
                line=line.strip()
                if not line:
                    if emp_line:
                        
                        new_section = True
                        if not first:
                            self.add_goal(name, curr_total, trans, incr)
                            trans=[]
                    else:
                        emp_line = True
                        
                    continue
                emp_line=False
                if new_section:
                    name, curr_total, incr = line.split(',')
                    curr_total = float(curr_total)
                    incr = float(incr)
                    first=False
                    new_section=False
                else:
                    trans.append(tuple(line.split(',')))
            prof.close()
        
    def add_goal(self, goalName, amount=0, trans=[], increment=0):
        self._goals.append(SavingGoal(goalName,amount, trans,increment))

    def remove_goal(self, index):
        self._goals.pop(index)

    def edit_goal(self, goalIndex, goalName, increment=0):
        
        self._goals[goalIndex].set_name(goalName)
        self._goals[goalIndex].set_increment(increment)

    def increment_all(self):
        for goal in self._goals:
            goal.increment()
    def set_increments(self, increments):
        for count, goal in enumerate(self._goals):
            goal.set_increment(increments[count])

    def get_increment_total(self):
        pay = 0
        for goal in self._goals:
            pay+=goal.get_increment()
        return pay

    

class InsufficientFunds(Exception):
    def __str__(self):
        return "There are insufficent funds in this fund to withdraw that amount"

class ViewMain(Frame):
    def __init__(self, master, goals):
        super().__init__(master)
        self._master= master
        self._goals=goals
        headingframe=Frame(self)
        headingframe.pack(fill=X)
        l1 = Label(headingframe, text="Account Balance: ", font=FONT)
        l1.pack(side="left", pady = 5)
        self._total = Label(headingframe, text="$0", font=FONT)
        self._total.pack(side="left")
        self._graph = Canvas(self, bg="white", relief=SUNKEN, bd=2)
        self._graph.pack(expand=True, fill=BOTH, pady=5)

        self._poollabels=Frame(self)
        self._poollabels.pack(fill=X,pady=5, padx=10)

        Button(self, text="Transfer between categories", command=self.transfer).pack()
        Button(self, text="Add Expense", command=self.expense).pack()
        Button(self, text="Add Lump Sum", command=self.lump).pack()
        Button(self, text="Transaction Lists", command=self.all_transactions).pack()
        Button(self, text="Increment to Next Period?", command=self.increment).pack(pady = 10)
        
        self._goal_labels = []
        self._goal_buttons = []
        self._trans = []
        
        self._graph.bind("<Configure>", lambda e: self.update())
        if self._goals.get_name():
            self.update()
        
    def transfer(self):
        categories = [x.get_name() for x in self._goals.get_goals()]
        self._popup = Toplevel()
        self._popup.grab_set()
        z = Frame(self._popup)
        z.pack(fill=X)
        Label(z,text="From: ").pack(side="left",expand=True)
        self._from = StringVar()
        selector = ttk.Combobox(self._popup, textvariable=self._from)

        selector['values'] = tuple(categories)
        selector.pack()

        z = Frame(self._popup)
        z.pack(fill=X)
        Label(z,text="From: ").pack(side="left",expand=True)
        self._to = StringVar()
        selector = ttk.Combobox(self._popup, textvariable=self._to)

        selector['values'] = tuple(categories)
        selector.pack()
        
        x = Frame(self._popup)
        x.pack(fill=X)
        Label(x,text="Amount: ").pack(side="left",expand=True)
        self._amount = Entry(x)
        self._amount.pack(expand=True)
        z = Frame(self._popup)
        z.pack(fill=X)
        Label(z,text="Reason: ").pack(side="left",expand=True)
        self._desc = Entry(z)
        self._desc.pack(expand=True)
        
        buttons = Frame(self._popup)
        buttons.pack(pady=5)
        save = Button(buttons, text="Commit", command=self.transfer_confirm)
        save.pack(side="left",padx=2)
        cancel = Button(buttons, text="Cancel", command=self._popup.destroy)
        cancel.pack(padx = 2)

    def transfer_confirm(self):
        categories = [x.get_name() for x in self._goals.get_goals()]
        amount, date, description = float(self._amount.get()),time.strftime("%d/%m/%Y"),self._desc.get()
        if amount>0:
            try:
                self._goals.get_goal(self._from.get()).modify(-1*amount, date, description)
            except InsufficientFunds as e:
                messagebox.showwarning("Error","Insufficient amount in category {0} to complete transfer".format(self._from.get()))
                return
            self._goals.get_goal(self._to.get()).modify(amount, date, description)
            self.update()
            self._popup.destroy()
        else:
            messagebox.showwarning("Error","Transfer amount must be positive")

    def expense(self):
        categories = [x.get_name() for x in self._goals.get_goals()]
        self._popup = Toplevel()
        self._popup.grab_set()

        z = Frame(self._popup)
        z.pack(fill=X)
        Label(z,text="Apply Expense to: ").pack(side="left",expand=True)
        self._to = StringVar()
        selector = ttk.Combobox(self._popup, textvariable=self._to)

        selector['values'] = tuple(categories)
        selector.pack()
        
        x = Frame(self._popup)
        x.pack(fill=X)
        Label(x,text="Amount: ").pack(side="left",expand=True)
        self._amount = Entry(x)
        self._amount.pack(expand=True)
        x = Frame(self._popup)
        x.pack(fill=X)
        Label(x,text="Date: ").pack(side="left",expand=True)
        self._date = Entry(x)
        self._date.pack(expand=True)
        self._date.insert(0,time.strftime("%d/%m/%Y"))
        z = Frame(self._popup)
        z.pack(fill=X)
        Label(z,text="Reason: ").pack(side="left",expand=True)
        self._desc = Entry(z)
        self._desc.pack(expand=True)
        
        buttons = Frame(self._popup)
        buttons.pack(pady=5)
        save = Button(buttons, text="Commit", command=self.expense_confirm)
        save.pack(side="left",padx=2)
        cancel = Button(buttons, text="Cancel", command=self._popup.destroy)
        cancel.pack(padx = 2)

    def expense_confirm(self):
        categories = [x.get_name() for x in self._goals.get_goals()]
        amount, date, description = float(self._amount.get()),self._date.get(),self._desc.get()
        if amount>0:
            try:
                self._goals.get_goal(self._to.get()).modify(-1*amount, date, description)
            except InsufficientFunds as e:
                messagebox.showwarning("Error","Insufficient amount in category {0} to complete transfer".format(self._to.get()))
                return
            self.update()
            self._popup.destroy()
        else:
            messagebox.showwarning("Error","Expense must be entered as a positive")

    def lump(self):
        categories = [x.get_name() for x in self._goals.get_goals()]
        self._popup = Toplevel()
        self._popup.grab_set()

        z = Frame(self._popup)
        z.pack(fill=X)
        Label(z,text="Apply Lump Sum to: ").pack(side="left",expand=True)
        self._to = StringVar()
        selector = ttk.Combobox(self._popup, textvariable=self._to)

        selector['values'] = tuple(categories)
        selector.pack()
        
        x = Frame(self._popup)
        x.pack(fill=X)
        Label(x,text="Amount: ").pack(side="left",expand=True)
        self._amount = Entry(x)
        self._amount.pack(expand=True)
        x = Frame(self._popup)
        x.pack(fill=X)
        Label(x,text="Date: ").pack(side="left",expand=True)
        self._date = Entry(x)
        self._date.pack(expand=True)
        self._date.insert(0,time.strftime("%d/%m/%Y"))
        z = Frame(self._popup)
        z.pack(fill=X)
        Label(z,text="Reason: ").pack(side="left",expand=True)
        self._desc = Entry(z)
        self._desc.pack(expand=True)
        
        buttons = Frame(self._popup)
        buttons.pack(pady=5)
        save = Button(buttons, text="Commit", command=self.lump_confirm)
        save.pack(side="left",padx=2)
        cancel = Button(buttons, text="Cancel", command=self._popup.destroy)
        cancel.pack(padx = 2)

    def lump_confirm(self):
        categories = [x.get_name() for x in self._goals.get_goals()]
        amount, date, description = float(self._amount.get()),self._date.get(),self._desc.get()
        if amount>0:
            self._goals.get_goal(self._to.get()).modify(amount, date, description)
            self.update()
            self._popup.destroy()
        else:
            messagebox.showwarning("Error","Lump Sum must be entered as a positive")
        
    def increment(self):
        self._goals.increment_all()
        self.update()
    
    def update(self):
        # Labels
        self._master.title("Budgeting Widget - {0}".format(self._goals.get_name()))
        self._total.config(text="${0}".format(round(self._goals.get_total(),4)))
        
        for i in range(len(self._goal_labels)):
            self._goal_labels[i].destroy()
        self._goal_labels = []
        longest_name = 0
        for goal in self._goals.get_goals():
            if len(goal.get_name())>longest_name:
                longest_name=len(goal.get_name())
        size = self._graph.winfo_width()/(longest_name*len(self._goals.get_goals()))
        for count,goal in enumerate(self._goals.get_goals(),0):
            self._goal_labels.append(Label(self._poollabels,wraplength=120 ,text="{0:<{1}}".format("{0}: ${1}".format(goal.get_name(), round(goal.get_amount(),4)),longest_name+10)))
            self._goal_labels[count].pack(expand=True, side="left", anchor = 'center')
        #Graph
        label_count = len(self._goal_labels)
        
        total = self._goals.get_total()
        width=self._graph.winfo_width()
        height=self._graph.winfo_height()
        split = width/(label_count*4)
        self._graph.delete(ALL)
        for count,goal in enumerate(self._goals.get_goals(),1):
            if goal.get_amount !=0 and total!=0:
                self._graph.create_rectangle([count*split+(count-1)*3*split, (1-goal.get_amount()/total)*height ,count*split+2*split+(count-1)*3*split, height],fill="blue")

    def all_transactions(self):
        categories = [x.get_name() for x in self._goals.get_goals()]
        self._transactions = []
        self._popup = Toplevel()
        self._popup.grab_set()
        self._trans_select = StringVar()
        selector = ttk.Combobox(self._popup, textvariable=self._trans_select)
        cat = ["All"]
        cat.extend(categories)
        selector['values'] = tuple(cat)
        selector.bind("<<ComboboxSelected>>",self.transactions)
        selector.current(0)
        selector.pack()
        closebutton = Button(self._popup, text="Close", command=self._popup.destroy)
        closebutton.pack(anchor="w")
        self.transactions('')
        
    def transactions(self, e):
        categories = [x.get_name() for x in self._goals.get_goals()]
        cat = self._trans_select.get()
        if cat=="All":
            name = Label(self._popup, text="Transactions for: All")
            name.pack()
            for goal in self._goals.get_goals():
                for transaction in goal.get_transactions():
                    x = Frame(self._popup)
                    x.pack(fill=X)
                    Label(x,text="Amount: ${0:<8}".format(transaction[0])).pack(side="left",expand=True)
                    Label(x, text="Date: {0}".format(transaction[1])).pack(side="left",expand=True)
                    Label(x,text="Description: {0}".format(transaction[2])).pack(side="left",expand=True)
        else:
            index = categories.index(cat)
            dates=['1/2/3']
            sorted(dates, key=lambda x:datetime.datetime.strptime(x,"%d/%m/%Y"))
            name = Label(self._popup, text="Transactions for:{0}".format(self._goals.get_index(index).get_name()))
            name.pack()
            for transaction in self._goals.get_index(index).get_transactions():
                x = Frame(self._popup)
                x.pack(fill=X)
                Label(x,text="Amount: ${0:<8}".format(transaction[0])).pack(side="left",expand=True)
                Label(x, text="Date: {0}".format(transaction[1])).pack(side="left",expand=True)
                Label(x,text="Description: {0}".format(transaction[2])).pack(side="left",expand=True)
           
    def profile_list(self):
        profiles = self._goals.get_profiles()
        self._popup = Toplevel()
        self._popup.grab_set()

        self._profile = StringVar()
        selector = ttk.Combobox(self._popup, textvariable=self._profile)

        selector['values'] = tuple(profiles)
        current = profiles.index(self._goals.get_name())
        selector.current(current)
        selector.pack()
        
        buttons = Frame(self._popup)
        buttons.pack(pady=5)
        save = Button(buttons, text="Load", command=self.load_profile)
        save.pack(side="left",padx=2)
        cancel = Button(buttons, text="Cancel", command=self._popup.destroy)
        cancel.pack(padx = 2)

    def load_profile(self):
        profile = self._profile.get()
        self._goals.load(profile)
        self.update()
        self._popup.destroy()

    def new_profile(self):
        self._popup = Toplevel()
        self._popup.grab_set()
        self._entry = Entry(self._popup)
        self._entry.pack()
        b1 = Button(self._popup, text="Create", command=self.add_profile)
        b1.pack()
        b2 = Button(self._popup, text="Cancel", command=self._popup.destroy)
        b2.pack()
        

    def add_profile(self):
        self._goals.new_profile(self._entry.get())
        self._master.title("Budgeting Widget - {0}".format(self._goals.get_name()))
        profs = open("profiles.list",'a')
        profs.write(self._goals.get_name()+"\n")
        profs.close()
        self._popup.destroy()

    def settings(self):
        self._settings = ViewSetting(self._goals,self)

    def config(self):
        self._popup = Toplevel()
        self._popup.grab_set()
        self._settings = []
        config = self._goals.get_config()
        for setting in config:
            temp = Frame(self._popup)
            temp.pack(fill=X)
            if setting == "default_profile":
                profiles = self._goals.get_profiles()
                self._comboval = StringVar()
                self._settings.append((Label(temp, text=setting),self._comboval))
                combo = ttk.Combobox(temp, textvariable = self._comboval)
                combo['values'] = tuple(profiles)
                combo.current(profiles.index(config[setting]))
                self._settings[-1][0].pack(side=LEFT)
                combo.pack()
            else:
                self._settings.append((Label(temp, text=setting),Entry(temp)))
                self._settings[-1][0].pack(side=LEFT)
                self._settings[-1][1].pack()
                self._settings[-1][1].insert(0, config[setting])

        Button(self._popup, text="Save Settings", command=self.save_config).pack()
        Button(self._popup, text="Cancel", command=self._popup.destroy).pack()
            

    def save_config(self):
        newconfig = {}
        oldconfig = self._goals.get_config()
        for setting, newval in self._settings:
            val = newval.get()
            setting = setting.cget("text")
            if val == "":
                newconfig[setting] = oldconfig[setting]
            else:
                newconfig[setting] = val
        self._goals.set_config(newconfig)
        self._master.minsize(self._goals.get_config().get("window_minsize_width","800"),self._goals.get_config().get("window_minsize_height","800"))
        self._popup.destroy()
        
        

class ViewSetting(Toplevel):
    def __init__(self, goals, parent):
        super().__init__()
        self.grab_set()
        self.minsize(500,500)
        self._parent=parent
        self._goals=goals
        l1 = Label(self, text="Budget Settings",font=FONT )
        l1.pack(anchor="w")
        one = Frame(self)
        one.pack(fill=X)
        Total = Label(one, text="Total Pay Amount")
        Total.pack(anchor="w", side="left")
        self._TotalAmt = Entry(one)
        self._TotalAmt.pack(anchor="w", side="left")
        self._labelentries = []
        self._categories = Frame(self)
        self._categories.pack(fill=X)
        self.update()
        saveb=Button(self, text="Save Settings", command=self.saveclose)
        saveb.pack(side="bottom")
        addCat = Button(self, text="Add Category", command=self.addCat)
        addCat.pack(side="bottom")
        delCat = Button(self, text="Remove Last Category", command=self.delCat)
        delCat.pack(side="bottom")
        
    def delCat(self):
        if len(self._goals.get_goals())>1:
            self._goals.remove_goal(-1)
            self.update()
        else:
            messagebox.showwarning("Cannot Remove!","Cannot remove Unallocated category")
    def saveclose(self):
        success = self.save()
        if success:
            self._parent.update()
            self.destroy()
  
        
    def save(self):
        increments=[]
        for index,(frame, name, entry) in enumerate(self._labelentries):
            if index != 0:
                increment = float(entry.get())
                nameofgoal = name.get()
                self._goals.edit_goal(index,nameofgoal,increment)
        total = self._goals.get_increment_total()-self._goals.get_index(0).get_increment()
        total=float(total)
        pay = float(self._TotalAmt.get())
        unallocate=True
        if total>pay:
            messagebox.showwarning("Overallocated!", "Sum of increments is greater than pay")
            unallocate = False
            return False
        self._goals.edit_goal(0, "Unallocated", round(pay-total,4))
        return True

    def addCat(self):
        self.save()
        self._goals.add_goal("")
        self.update()
        
    def update(self):
        for frame,name,entry in self._labelentries:
            frame.destroy()
        self._labelentries=[]
        pay = 0
        for count, goal in enumerate(self._goals.get_goals()):
            tmp = Frame(self._categories)
            pay += goal.get_increment()
            if count == 0:
                nm = Label(tmp, text=goal.get_name())
                ent = Label(tmp, text=goal.get_increment())
            else:
                nm = Entry(tmp)
                ent = Entry(tmp)
                nm.insert(0,goal.get_name())
                ent.insert(0,goal.get_increment())
            self._labelentries.append((tmp,nm,ent))
        for frame,name, entry in self._labelentries:
            frame.pack(fill=X, pady=2, padx=2)
            name.pack(side="left",padx=5, expand=True)
            entry.pack(side="left", expand=True)
        self._TotalAmt.delete(0,END)
        self._TotalAmt.insert(0,round(pay,4))

class View(object):
    def __init__(self, master, model):
        self._master = master
        self._model = model
        
        self._master.minsize(self._model.get_config().get("window_minsize_width","800"),self._model.get_config().get("window_minsize_height","800"))
        self._master.title("Budgeting Widget - {0}".format(self._model.get_config().get("default_profile")))
        #self._master.attributes('-fullscreen', True)
        
        
        self._display = ViewMain(self._master, self._model)
        self._display.pack(fill=BOTH, expand=True)

        #menubar
        menubar = Menu(self._master)
        filemenu= Menu(menubar,tearoff=0)
        editmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File",menu=filemenu)
        menubar.add_cascade(label="Edit",menu=editmenu)
        editmenu.add_command(label="Profile Settings", command=self._display.settings)
        editmenu.add_command(label="Configuration", command=self._display.config)
        filemenu.add_command(label="New Profile", command=self._display.new_profile)        
        filemenu.add_command(label="Load Profile", command=self._display.profile_list)
        filemenu.add_separator()
        filemenu.add_command(label="Save", command=self._model.save)
        filemenu.add_command(label="Save & Quit", command=self.close)
        filemenu.add_command(label="Quit", command=self._master.destroy)
        self._master.config(menu=menubar)

        try:
            if self._model.get_config().get("default_profile","") == "":
                self._display.new_profile()
            else:
                self._model.load(self._model.get_config().get("default_profile"))
            
        except Exception:
            self._config["default_profile"] = ""

    def close(self):
        self._model.save()
        self._master.destroy()

class ControllerApp(object):
    def __init__(self, master):
        self._master = master      
        #model
        self._model = Goals()

        #Display
        self._display = View(self._master, self._model)




    


if __name__ == '__main__':
    root = Tk()
    app = ControllerApp(root)
    root.mainloop()
    
