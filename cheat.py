class Cheat:
    def __call__(self, command, robot):
        if command == 'makebeeper':
            robot.world.robotBeepers += 1
        elif command == 'breakpoint':
            robot.gui.breakpoint()
        elif command in robot.gui.SleepDict.keys():
            robot.gui.setSpeed(command)
        else:
            print 'unrecognized cheat', command
