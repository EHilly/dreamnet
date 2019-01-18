from time import sleep

from dreamnet.scene import Scene

def printHelp():
	print("Type the name of an object to interact with it.")
	print("Type 'dream' to go somewhere else.")
	print("Type 'look' to look around.")
	print("Type 'help' to see these commands again.")
	print("Type 'quit' to wake up.")

def introText(topic):	
	print("You think of {} and close your eyes.".format(topic))
	sleep(0.7)
	print("Other thoughts ebb in and out of your mind,")
	sleep(0.7)
	print("getting more dim and more distant.")
	sleep(0.7)
	print("You drift off.....")
	sleep(0.7)
	
	for n in range(4,-1,-1): 
		print('.'*n)
		sleep(1.1-0.1*n)

def main():
	beginning = input("What do you want to dream about?\n")
	introText(beginning if beginning else "nothing")
	sc = Scene()
	sc.dream(beginning)
	print("(Type 'help' to see a list of commands.)")

	inp = input("\n>")
	while inp != "quit":
		if inp == "help": printHelp()
		else: sc.handleInput(inp)
		
		inp = input("\n>")

if __name__ == "__main__":
	main()