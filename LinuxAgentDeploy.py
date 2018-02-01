import getpass
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "\\Utilities")
print(sys.path)
from UsefulUtilities import Utils


#def OpenSshConnection(i_Address, i_UserName, i_Password)

def RunRemoteCommand(i_SshSession, i_CommandToExecute):
    commandToExecute = i_CommandToExecute[0]
    errorsToExclude = i_CommandToExecute[1]
    try:
        stdin, stdout, stderr = i_SshSession.exec_command(commandToExecute, get_pty=True)
        returnCode = stdout.channel.recv_exit_status()
        output = [line for line in stdout.readlines()]
        if returnCode != 0:
            if any(stringToExclude in str(output) for stringToExclude in errorsToExclude):
                pass
            else:
                raise Exception(output)
        return output
    except Exception as e:
        raise Exception("Error : Something went wrong with the command : \n" + str(commandToExecute) + "\n" +
                        str(e.args[0]) + "\nExiting with code  9!", 9)


def executeCommands(i_CommandsToExecute, i_sshSession):
    for command in i_CommandsToExecute:
        try:
            print("Going to run the following command : {}".format(command[0]))
            [print(line) for line in RunRemoteCommand(i_sshSession, command)]
            print("*********************\n")
        except Exception as e:
            raise
    return 0

def Main(linuxUserName, i_sshSession):
    installBaseLocation = "/usr/share/Installs/bmc/control-m/"
    '''
        below is list of tuples, the first cell is the command while the second cell
        is a list of messages to be exclude if arrived
    '''
    commandsToExecute = [
        ("{}FullInstallations/Agent/latest/Unix/setup.sh -silent {}".format(installBaseLocation, installBaseLocation + xmlLoc),
                                                            ["already installed"]),
        # The source command is for the $PATH Building
        ("source ~/.bash_profile; ~/ctm/scripts/shut-ag -u ctmuser -p ALL",""),
        ("source ~/.bash_profile; echo 'y' | {}FPs/Agent/latest/Unix/setup.sh".format(installBaseLocation),
                                                            ["already installed"]),
        ("source ~/.bash_profile; echo 'y' | sudo set_agent_mode -u {} -o 2".format(linuxUserName),""),
        ("source ~/.bash_profile; {}SSL/Certs/Internal_EM_Certs/Certificate_for_CONTROL-M_Agent/setup.sh".format(installBaseLocation),"")
    ]
    try:
        executeCommands(commandsToExecute, i_sshSession)
    except:
        raise
    modulesInstallationProps = [
        ("AFT", ("source ~/.bash_profile; {0}Modules/AFT/GA-latest/setup.sh -silent {0}Modules/AFT/GA-latest/AFT.xml".format(installBaseLocation), "already installed"),
         ("source ~/.bash_profile; {}Modules/AFT/FP-latest/Unix/setup.sh -s".format(installBaseLocation), "already installed")),
        ("DB", ("source ~/.bash_profile; {0}Modules/DB/GA-latest/setup.sh -silent {0}Modules/DB/GA-latest/DB.xml".format(installBaseLocation), "already installed")),
        ("OEBS", ("source ~/.bash_profile; {0}Modules/OEBS/GA-latest/setup.sh -silent {0}Modules/OEBS/GA-latest/OEBS.xml".format(installBaseLocation), "already installed"))
    ]
    blankOrAnother = ""
    while True:
        cmInstallationAnswer = input("Do you want to install {} CM on this Agent?".format(blankOrAnother))
        if cmInstallationAnswer in yesAnswer:
            blankOrAnother = "another"
            cmType = input('What CM you want to Install? [DB/AFT/OEBS] : ')
            askForCmType = True
            while askForCmType:
                if cmType in [cmName[0] for cmName in modulesInstallationProps]:
                    askForCmType = False

            indexOfCmTuple = [tupleVar[0] for tupleVar in modulesInstallationProps].index(cmType)
            commandsToExecute = modulesInstallationProps[indexOfCmTuple][1:]
            try:
                executeCommands(commandsToExecute,i_sshSession)
            except:
                raise
        elif cmInstallationAnswer in noAnswer:
            print('No CM will be installed!')
            break
        else:
            print("Wrong Selection!")
            continue
    else:
        print('OKey....Bye')
    return

def AddNewAgent(i_ServerName, i_sshSession):
    commandsToExecute = [
        ("ctmping -nodeid {} -nodetype REGULAR -discover y".format(i_ServerName),),
        ("ctmgetcm -NODEID {} -APPLTYPE \"*\" -ACTION get".format(i_ServerName),)
    ]
    try:
        executeCommands(commandsToExecute, i_sshSession)
    except:
        raise

if __name__ == "__main__":
    print("****** Welcome to Agent Deployment program ******")
    serverName = input('Enter Server Name for Installation: ')
    envAskFlag = True
    while  envAskFlag:
        env = input('Please enter environment [Prod/Test] the CTM Agent will be connected: ')
        if env in ['Prod', 'prod', 'p', 'P']:
            CTMServer = 'pctmpapp9'
            xmlLoc = '9ProdLinux.xml'
            envAskFlag = False
        elif env in ['Test', 'test', 'T', 't']:
            CTMServer = 'pctmtapp9'
            xmlLoc = '9TestLinux.xml'
            envAskFlag = False
        else:
            print("Wrong Selection!")
    xmlLoc = "FullInstallations/Agent/latest/Unix/" + xmlLoc
    linuxUserName = 'ctmuser'
    linuxPassword = getpass.getpass("Enter Password For ctmuser : ")
    yesAnswer = ['y', 'Y', 'yes', 'Yes', 'YES']
    noAnswer = ['n', 'N', 'No', 'no', 'NO']
    try:
        # Trying to establish SSH connection to the host to be the Agent and getting the session to work with afterwards
        sshSession = Utils.linuxConnector(serverName, linuxUserName, linuxPassword)
        print("Connections Established to host {}!".format(serverName))
        Main(linuxUserName, sshSession)
        sshSession.close()
        sshSession = Utils.linuxConnector(CTMServer, linuxUserName, linuxPassword)

    except Exception as e:
        exception = e.args[0]
        print(exception)
        if len(e.args) > 1 :
            exitCode = e.args[1]
            exit(exitCode)
        else:
            raise
    finally:
        if sshSession:
            sshSession.close()


    input("Don't forget to set automatic startup for the agent!")

