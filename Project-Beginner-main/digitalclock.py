import time 
import sys 
def userchoice(choice):
    if choice == 1:
        digial_clock()
    elif choice == 2:
        seconds = int(input("enter the number of seconds to countdown: "))
        countdown_timer(seconds)
    else:
        print("invalid choice")
def digial_clock():
    '''display a digital clock'''
    while True:
        current_time = time.localtime()
        time_string = time.strftime("%Y-%m-%d %H:%M:%S", current_time)
        print(f"\rCurrent time : {time_string}", end='', flush=True) 
        time.sleep(1)
        

def countdown_timer(seconds):
    '''countdown timer'''
    print("countdown timer started")
    while seconds >0:
        print("\rtime remaining: "+str(seconds)+" seconds", end='')
        time.sleep(1)
        seconds-2=1
    print("\ntime is up")
if __name__ == "__main__":
    while True:
        choice = int(input("choose an option 1: digital clock, 2: countdown timer"))
        userchoice(int(choice))