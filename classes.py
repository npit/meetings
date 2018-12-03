import pandas
import pickle

def matches(arg1, arg2):
    if arg1 == arg2: return True
    if arg1.startswith(arg2[0]): return True
    return False

class Week:
    hourchunk = 1
    limit_up = 21
    limit_down = 9
    after = "after"
    before = "before"
    can = "can"
    cant = "cant"
    symbols = {"can": "OK", "cant": "X"}
    person = None
    restrictions = []
    availability = []
    weekdays = ["mon", "tue", "wed", "thu", "fri"]

    def aggregate(weeks):
        agg_week = Week("aggregate")
        agg_week.initialize_availability(Week.can)
        timerange = agg_week.timerange

        with_restrictions = 0

        agg_week = pandas.DataFrame(agg_week.availability).replace(Week.symbols[Week.cant], 0)
        for w in weeks:
            if not w.restrictions:
                continue
            with_restrictions += 1
            wnumeric = pandas.DataFrame(w.availability).replace(Week.symbols[Week.can], 1).replace(Week.symbols[Week.cant], 0)
            agg_week += wnumeric
            pass
        print("{} people in total, {} of which with restrictions".format(len(weeks), with_restrictions))
        agg_week = pandas.DataFrame(agg_week.values.transpose(), index = timerange, columns = Week.weekdays)
        print(agg_week)


    # week variables
    def time2float(self, timestr):
        if len(timestr) == 2:
            return int(timestr)
        print("Invalid time", timestr)
        exit(1)

    def get_avail(self):
        # convert to hourwise
        return list(map(list, zip(* self.availability)))

    def initialize_availability(self, value):
        if value == self.can: symbol = self.symbols[self.cant]
        else: symbol = self.symbols[self.can]
        self.availability = [ [symbol for _ in self.timerange] for _ in range(5)]

    def __init__(self, name):
        self.restrictions = []
        self.availability = []
        self.name = name
        self.timerange = range(self.limit_down, self.limit_up + self.hourchunk, self.hourchunk)
        # indexes from day times to integer indexes
        self.time2int = {}
        for t in self.timerange:
            self.time2int[t] = len(self.time2int)

    def wipe(self):
        self.restrictions = []
        self.availability = []

    def change(self, day, time1, time2, value, relational):
        # check initialization
        if not self.restrictions:
            # initialize to inverse of restriction
            self.initialize_availability(value)


        if time1 is None and time2 is None:
            time1 = self.limit_down
            time2 = self.limit_up

        if time1 and time1 not in self.time2int:
            print("Require hours in 24h format, got {} instead.".format(time1))
            exit(1)

        if time2 and time2 not in self.time2int:
            print("Require hours in 24h format, got {} instead.".format(time2))
            exit(1)

        if time2 == None:
            if relational == self.after:
                time2 = self.limit_up
            elif relational == self.before:
                time2 = time1 - self.hourchunk
                time1 = self.limit_down
            else:
                time2 = time1

        self.restrictions.append((value, self.weekdays[day], time1, time2))
        #print(self.restrictions[-1])

        for t in range(time1, time2+self.hourchunk, self.hourchunk):
            timeidx = self.time2int[t]
            #print("Setting day {} time {} idx {} to {}".format(day, t, timeidx, value))
            self.availability[day][timeidx] = self.symbols[value]

    def pretty_print(self):
        w = pandas.DataFrame(self.get_avail(), index = self.timerange, columns = self.weekdays)
        print(w)


class Schedule:
    command_handlers = {}
    person_weeks = {}
    weekdays = Week.weekdays #["mon", "tue", "wed", "thu", "fri"]
    temporal_restrictors = None
    availability_keywords = None
    # limits = [datetime.strptime('09:00'), datetime.strptime('21:00')]
    keywords = ["tables", "restrictions", "people", "aggregate"]

    do_quit = False
    verbose = False

    def __init__(self, name):
        self.after = Week.after
        self.before = Week.before
        self.name = name
        self.availability_keywords = [Week.can, Week.cant]
        self.temporal_restrictors = [self.after, self.before]

    def show_restrictions(self, which_person = None):
        if which_person is None:
            print("Restrictions:")
        for pers, week in self.person_weeks.items():
            if which_person and pers != which_person:
                continue
            print(pers)
            for rest in week.restrictions:
                print("\t{}".format(rest))
            if which_person:
                return

    def show_tables(self, which_person = None):
        if which_person is None:
            print("Tables:")
        for pers, week in self.person_weeks.items():
            if which_person and pers != which_person:
                continue
            print("Table for {}".format(pers))
            week.pretty_print()
            if which_person:
                return

    def should_quit(self):
        return self.do_quit

    def parse_misc(self, command):
        if matches(command, "quit"):
            self.do_quit = True
            return True
        cmds = command.split()
        cmd = cmds[0]


        if matches(cmd, "show"):
            if len(cmds) == 1:
                self.show_restrictions()
                self.show_tables()
                return True

            args = cmds[1:]
            arg = args[0]

            if not any(matches(arg, kw) for kw in self.keywords):
                # it's a person
                if arg not in self.person_weeks:
                    print("Person {} does not exist.".format(arg))
                which = args[1] if len(args) > 1 else None
                if which is None or matches(which, "restrictions"):
                    self.show_tables(arg)
                if which is None or matches(which, "restrictions"):
                    self.show_restrictions(arg)
                return True


            which = args[1] if len(args) > 1 else None
            if matches(arg, "restrictions"):
                self.show_restrictions(which)
                return True
            elif matches(arg, "tables"):
                self.show_tables(which)
                return True
            elif matches(arg, "people"):
                for pers in self.person_weeks:
                    print(pers)
                return True
            elif matches(arg, "aggregate"):
                self.show_aggregate()
                return True

        return False

    def parse(self, command):
        if not command:
            return

        if self.parse_misc(command):
            return

        print("Parsing command:", command)
        command = command.split()
        name = command[0]
        if len(name) < 2:
            print("Names need to exceed a single character.")
            exit(1)
        if name in self.keywords:
            print("Name {} is a reserved keyword.".format(name))
            exit(1)

        if name in self.availability_keywords:
            # no name give, name cache in effect.
            name = self.person_cache
        else:
            if len(command) == 1:
                self.person_cache = name
                print("Taking input for", name)
                self.person_weeks[name] = Week(name)
                return
            command = command[1:]
        keyword = command[0]
        if keyword == "clear":
            if name not in self.person_weeks:
                print("Huh? No data for {}.".format(name))
                return
            self.person_weeks[name].wipe()
            return
        if keyword == "delete":
            if name not in self.person_weeks:
                print("Huh? No data for {}.".format(name))
                return
            del self.person_weeks[name]
            return

        restr = [ c.lower() for c in command[1:]]

        self.person_cache = name
        if name not in self.person_weeks:
            print("Creating week for {}".format(name))
            self.person_weeks[name] = Week(name)
        self.process_temporal_command(name, keyword, restr)
        return False

    # weekday specifier, duration specifier
    # weekday specifier: day name / abbrev
    # duration specifier: time1-time2
    # duration specifier: <after|before|...> time
    def process_temporal_command(self, person, avail, cmd):
        print("Processing temporal command", cmd)
        weekday = self.weekdays.index(self.get_weekday(cmd[0]))
        print("Day index for {} is {}".format(cmd[0], weekday))

        if len(cmd) == 1:
            self.person_weeks[person].change( weekday, None, None, avail, None)
            return

        if cmd[1] in self.temporal_restrictors:
            restrictor = cmd[1]
            timest = self.get_time(cmd[2])
            self.person_weeks[person].change(weekday, timest, None, avail, restrictor)
            return

        time1, time2 = self.get_timespan(cmd[1:])
        self.person_weeks[person].change( weekday, time1, time2, avail, None)

    def get_timespan(self, timestr):
        print("Getting timespan for ", timestr)
        range_delimiters = ["-", "to"]
        if len(timestr) == 1:
            # string, like 12-13 or 9to10
            timestr = timestr[0]
            for delim in range_delimiters:
                if delim in timestr:
                    t1, t2 = list(map(lambda x : x.strip(), timestr.split(delim)))
                    return self.get_time(t1), self.get_time(t2)

        for delim in range_delimiters:
            if delim in timestr:
                idx = timestr.index(delim)
                t1, t2 = timestr[:idx][0], timestr[idx+1:][0]
                return self.get_time(t1), self.get_time(t2)
        # else a single number
        t1 = timestr.split()

    def get_time(self, timestr):
        if timestr is None:
            return None
        timest = float(timestr)
        assert int(timest) == timest, "Need int times, got {} instead.".format(timest)
        timest = int(timest)
        return timest

    def get_weekday(self, wstr):
        if wstr in self.weekdays:
            return wstr
        print("Undefined weekday:", wstr)
        exit(1)

    def load(path):
        with open(path, "rb") as f:
            data = pickle.load(f)
            name, pers_weeks = data
            sched = Schedule(name)
            sched.person_weeks = pers_weeks
        return sched

    def save(self):
        with open(self.name, "wb") as f:
            print("Saving schedule.")
            pickle.dump([self.name, self.person_weeks], f)

    def print_week(self):
        if self.verbose:
            for person in self.person_weeks:
                week = self.person_weeks[person]
                self.show_restrictions(person)
                self.show_tables(person)
                #print(week.name, week.restrictions)
                week.pretty_print()
        self.show_aggregate()

    def show_aggregate(self):
        # print aggregate
        print("Aggregate table:")
        Week.aggregate(self.person_weeks.values())

    def set_verbose(self):
        self.verbose = True
