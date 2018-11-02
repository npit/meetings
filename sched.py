import argparse
from os.path import exists
import pickle
from classes import Schedule
# desired functionality:
# sched <schedule name> // now the reference is on that schedule, everything following concerns it
# sched person can <temporal segment> | cant <temporal segment> // write down available / not available time slice
# // ^ can X => means cannot at y where y!=X
# // ^ cant X => means can at y where y!=X

# sched person // list can and cants
# sched set duration // or sth. set meeting duration
# sched compute // or sth. compute candidate datetimes. show if all can at that time. decreasing order of can-ness

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("schedule_name")
    parser.add_argument("--verbose", action="store_true", dest="verbose")
    args = parser.parse_args()

    schedule_name = args.schedule_name
    if exists(schedule_name):
        print("Loading existing schedule.")
        schedule = Schedule.load(schedule_name)
        schedule.print_week()
        print("Loaded {}.".format(schedule.name))
    else:
        print("Creating new schedule: {}".format(schedule_name))
        schedule = Schedule(schedule_name)
    if args.verbose:
        schedule.set_verbose()
    # cmds = []
    # cmds.append( "mary cant Mon after 14")
    # cmds.append( "kate cant Tue  14 - 15")
    # cmds.append( "john cant Tue  before 10")
    # cmds.append( "mary cant Fri 9 to 18")

    while(True):
        print("> ",end="")
        cmd = input()
        #command = "john can Mon after 14"
        #if not cmds:
        #    break
        #cmd = cmds.pop()
        #print(cmd)
        schedule.parse(cmd)
        schedule.print_week()
        if schedule.should_quit():
            break
        #break

    schedule.print_week()

    # save schedule
    schedule.save()



if __name__ == "__main__":
    main()
