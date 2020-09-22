import requests

url = 'http://localhost:8000'
MAX_CAPACITY = 8

def start(user, problem, count):
    uri = url + '/start/' + user + '/' + str(problem) + '/' + str(count)
    return requests.post(uri).json()

def oncalls(token):
    uri = url + '/oncalls'
    return requests.get(uri, headers={'X-Auth-Token': token}).json()

def action(token, cmds):
    uri = url + '/action'
    return requests.post(uri, headers={'X-Auth-Token': token}, json={'commands': cmds}).json()

def get_query(idx, cmd):
    if type(cmd) is tuple:
        return {'elevator_id': idx, 'command': cmd[0], 'call_ids': cmd[1]}
    return {'elevator_id': idx, 'command': cmd}

class Elevator:
    def __init__(self):
        self.state = 'STOPPED'
        self.passengers = []
        self.waitings = []
        self.floor = 1
        self.start = 0
        self.end = 0

    def has_space(self):
        return len(self.passengers) + len(self.waitings) < MAX_CAPACITY

    def add_waiting(self, call):
        if self.start == self.end:
            self.start = call['start']
            self.end = call['end']
        self.waitings.append(call)

    def get_command(self):
        get_in = [wait for wait in self.waitings if wait['start'] == self.floor]
        get_out = [pas for pas in self.passengers if pas['end'] == self.floor]

        if self.state == "STOPPED":
            if len(get_in) or len(get_out):
                self.state = "OPENED"
                return "OPEN"

            if len(self.waitings):
                if self.waitings[0]['start'] < self.floor:
                    self.state = "DOWNWARD"
                    self.floor -= 1
                    return "DOWN"
                else:
                    self.state = "UPWARD"
                    self.floor += 1
                    return "UP"
            if len(self.passengers):
                if self.passengers[0]['end'] < self.floor:
                    self.state = "DOWNWARD"
                    self.floor -= 1
                    return "DOWN"
                else:
                    self.state = "UPWARD"
                    self.floor += 1
                    return "UP"

            self.start = self.floor
            self.end = self.floor
            self.state = "STOPPED"
            return "STOP"

        elif self.state == "UPWARD":
            if len(get_in) or len(get_out):
                self.state = "STOPPED"
                return "STOP"

            self.state = "UPWARD"
            self.floor += 1
            return "UP"

        elif self.state == "DOWNWARD":
            if len(get_in) or len(get_out):
                self.state = "STOPPED"
                return "STOP"

            self.state = "DOWNWARD"
            self.floor -= 1
            return "DOWN"

        elif self.state == "OPENED":
            if len(get_in):
                self.passengers.extend(get_in)
                self.waitings = [wait for wait in self.waitings if wait['start'] != self.floor]
                return "ENTER", [c['id'] for c in get_in]

            if len(get_out):
                self.passengers = [pas for pas in self.passengers if pas['end'] != self.floor]
                return "EXIT", [c['id'] for c in get_out]

            self.state = "STOPPED"
            return "CLOSE"

    def __str__(self):
        return "Floor: " + str(self.floor) + ", " + str(self.start) + "->" + str(self.end) + \
                "\nPassengers: " + str([p['id'] for p in self.passengers]) + \
                "\nWaiting: " + str([w['id'] for w in self.waitings]) + \
                "\nState: " + self.state + \
                "\n"

if __name__ == '__main__':
    username = 'juseong'
    problem = 2 # 0, 1, 2
    count = 4 # 1, 2, 3, 4

    elevators = [Elevator() for i in range(count)]
    start_req = start(username, problem, count)
    token = start_req['token']
    done = set()

    epoch = 0
    while True:
        calls = oncalls(token)
        if calls['is_end']:
            break

        commands = []
        new_calls = [call for call in calls['calls'] if call['id'] not in done]
        print(new_calls)
        for idx, elevator in enumerate(elevators):
            print(elevator)
            if elevator.has_space() and len(new_calls):
                if elevator.start < elevator.end: # STATE: UPWARD
                    copy_calls = new_calls[:]
                    for call in copy_calls:
                        if elevator.has_space() and elevator.floor <= call['start'] < call['end']:
                            elevator.add_waiting(call)
                            done.add(call['id'])
                            new_calls.remove(call)

                elif elevator.start > elevator.end: # STATE: DOWNWARD
                    copy_calls = new_calls[:]
                    for call in copy_calls:
                        if elevator.has_space() and call['end'] < call['start'] <= elevator.floor:
                            elevator.add_waiting(call)
                            done.add(call['id'])
                            new_calls.remove(call)

                elif elevator.start == elevator.end: # STATE: STOPPED
                    elevator.add_waiting(new_calls[0])
                    done.add(new_calls[0]['id'])
                    new_calls.pop(0)

            next_command = elevator.get_command()
            commands.append(get_query(idx, next_command))

        print("Epoch:", epoch)
        if len(commands):
            print(commands)
            result = action(token, commands)
        epoch += 1
        
print("COMPLETED", epoch)
