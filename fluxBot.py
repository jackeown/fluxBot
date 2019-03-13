#!/usr/bin/python3
import time
import melee
import argparse
import signal
import sys

from code import interact

# from fluxBot import ai
from fluxBot import simpleAI as ai
# from fluxBot import superSimpleAI as ai


def check_port(value):
    """Verifies valid 1-4 gamecube controller port"""
    ivalue = int(value)
    if ivalue < 1 or ivalue > 4:
         raise argparse.ArgumentTypeError("%s is an invalid controller port. \
         Must be 1, 2, 3, or 4." % value)
    return ivalue

# There WILL be EXACTLY 2 players.
# The first player (Port 1) can be a HUMAN or a BOT
# The second player (Port 2) MUST BE A BOT

chain = None
parser = argparse.ArgumentParser(description='A bot made by John McKeown using libmelee and Tensorflow.')
parser.add_argument('--port1', '-p1', type=check_port,
                    help='The controller port AI #1 (or you if the human flag is enabled) will play on',
                    default=1)
parser.add_argument('--port2', '-p2', type=check_port,
                    help='The controller port AI #2 will play on.',
                    default=2)
parser.add_argument('--debug', '-d', action='store_true',
                    help='Debug mode. Creates a CSV of all game state')
parser.add_argument('--framerecord', '-R', default=False, action='store_true',
                    help='Records frame data from the match, stores into framedata.csv')
parser.add_argument('--human', '-q', default=False, action='store_true',
                    help='If true, port1 is a human instead of an AI')
parser.add_argument('--live', '-l', default=False, action='store_true',
                    help='The opponent is playing live with a GCN Adapter',)
parser.add_argument('--train', '-t', default=False, action='store_true',
                    help='If true, the ai will be trained during play, else not.')
parser.add_argument('--speed', '-s', default=1.0,
                    help='Speed relative to normal gameplay speed at which to emulate the game')
parser.add_argument('--render', '-r', default=False, action='store_true')
parser.add_argument('--builtinai', default=False, action='store_true')
args = parser.parse_args()

log = None
if args.debug:
    log = melee.logger.Logger()

framedata = melee.framedata.FrameData(args.framerecord)

#Options here are:
#   "STANDARD" input is what dolphin calls the type of input that we use
#       for named pipe (bot) input
#   GCN_ADAPTER will use your WiiU adapter for live human-controlled play
#   UNPLUGGED is pretty obvious what it means
#
# opponent_type = melee.enums.ControllerType.UNPLUGGED
if args.human and args.live:
    port1_controller_type = melee.enums.ControllerType.GCN_ADAPTER
else:
    port1_controller_type = melee.enums.ControllerType.STANDARD


# Create our Dolphin object. 
# This will be the primary object that we will interface with
dolphin = melee.dolphin.Dolphin(ai_port=args.port2, opponent_port=args.port1,
    opponent_type=port1_controller_type, logger=log, human=args.human, emuSpeed=args.speed)

# Create our GameState object for the dolphin instance
gamestate = melee.gamestate.GameState(dolphin)

# Create our Controller objects that we can press buttons on
if not args.human:
    controller1 = melee.controller.Controller(port=args.port1, dolphin=dolphin)
controller2 = melee.controller.Controller(port=args.port2, dolphin=dolphin)


def signal_handler(signal, frame):
    dolphin.terminate()
    if args.debug:
        log.writelog()
        print("")  # because the ^C will be on the terminal
        print("Log file created: " + log.filename)
    print("Shutting down cleanly...")
    if args.framerecord:
        framedata.saverecording()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Run dolphin and render the output
print("RENDER: {}".format(args.render))
dolphin.run(render=args.render,
            iso_path="/home/user/dolphin_roms/Original/SSBM.iso")

# Plug our controller in
#   Due to how named pipes work, this has to come AFTER running dolphin
#   NOTE: If you're loading a movie file, don't connect the controller,
#   dolphin will hang waiting for input and never receive it
if not args.human:
	controller1.connect()
controller2.connect()

myAI = ai.AI(loadAndSave=True, train=args.train)

stageForSelectingDifficulty = 1
startTime = time.time()
started = False

# Main loop
while True:
    # "step" to the next frame
    gamestate.step()
    if gamestate.frame < 3 and not started:
        continue
    else:
        started = True

    if(gamestate.processingtime * 1000 > 12):
        print("WARNING: Last frame took " + str(gamestate.processingtime*1000) + "ms to process.")

    # What menu are we in
    if gamestate.menu_state == melee.enums.Menu.IN_GAME:
        # This is where your AI does all of its stuff!
        # This code block will get hit once per frame, so here is where you read
        # in the gamestate and decide what buttons to push on the controllers
        # interact(local=locals())
        if (not args.human) and (not args.builtinai):
           myAI.makeMove(gamestate, controller1)
            # melee.techskill.multishine(gamestate.opponent_state, controller1)
        # melee.techskill.multishine(gamestate.ai_state, controller2)
        myAI.makeMove(gamestate, controller2, ai_number = 2)

    #  If we're at the character select screen, choose our character
    elif gamestate.menu_state == melee.enums.Menu.CHARACTER_SELECT:
        print("Character Select")

        # P2 picks Fox.
        melee.menuhelper.choosecharacter(character=melee.enums.Character.FOX,flipped=False,
            gamestate=gamestate, controller=controller2, swag=False, start=False)


        if not args.human:
            setupTime = 10 # seconds
            setupTime *= 60 # don't change this.
            if gamestate.frame % setupTime < setupTime // 4:
                melee.menuhelper.choosecharacter(character=melee.enums.Character.FOX,flipped=True,
                        gamestate=gamestate, controller=controller1, swag=False, start=False)

            elif (gamestate.frame % setupTime < 2*setupTime // 4) and args.builtinai:
                melee.menuhelper.changecontrollerstatus(controller=controller1, 
                    gamestate=gamestate,
                    port = args.port1, status = melee.enums.ControllerStatus.CONTROLLER_CPU,
                    flipped = True, character = melee.enums.Character.FOX)

            elif (gamestate.frame % setupTime < 3*setupTime // 4) and args.builtinai:
                stageForSelectingDifficulty = melee.menuhelper.setAILevel(controller = controller1,
                    gamestate = gamestate, port = args.port1, level = 9, flipped = True, 
                    stage = stageForSelectingDifficulty)

            elif gamestate.frame % setupTime < setupTime:
                controller1.press_button(melee.enums.Button.BUTTON_START)

    # If we're at the postgame scores screen, spam START
    elif gamestate.menu_state == melee.enums.Menu.POSTGAME_SCORES:
        print("Postgame Scores")
        if not args.human:
            melee.menuhelper.skippostgame(controller=controller1)
        melee.menuhelper.skippostgame(controller=controller2)

    # If we're at the stage select screen, choose a stage
    elif gamestate.menu_state == melee.enums.Menu.STAGE_SELECT:
        print("Stage Select")
        if not args.human:
            controller1.empty_input()
        melee.menuhelper.choosestage(stage=melee.enums.Stage.FINAL_DESTINATION,
            gamestate=gamestate, controller=controller2)

    # Flush any button presses queued up
    if not args.human:
        controller1.flush()
    controller2.flush()
    if log:
        log.logframe(gamestate)
        log.writeframe()
