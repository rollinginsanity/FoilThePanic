import socket
import time
def main():

    ftp = FoilThePanic("127.0.0.1", 21)
    ftp.connect()
    userName = input("Username for le FTP server plz: ")
    password = input("Password for le aforementioned FTP server pls: ")
    ftp.login(userName, password)
    print(ftp.pwd())
    print(ftp.listFiles())
    ftp.close()

class FoilThePanic():
    #Class vars for connecting to our FTP server.
    ftpControlSocket = None
    host = None
    port = None

    #And here's a bunch of strings for the commands.
    USERCOMMAND = "USER "
    PASSCOMMAND = "PASS "
    PWDCOMMAND = "PWD"
    CWDCOMMAND = "CWD"
    PASSIVECOMMAND = "PASV"
    LISTCOMMAND = "LIST"

    #Set our host and port.
    def __init__(self, host, port):
        self.host = host
        self.port = port

    #Connect to the FTP server. 
    #TODO, add decent error handling if a conenction fails.
    def connect(self):
        self.ftpControlSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ftpControlSocket.connect((self.host, self.port))
        self.serverResponse(self.ftpControlSocket.recv(1024).decode())
    

    
    ##############
    #Connection related functions here.
    ##############

    def serverResponse(self, response):
        print(response)

    #Adds a "\n" to every string. Saves having to add it to every string.
    def buildFTPCmd(self, command, input):
        return (command+input+"\n").encode()

    def sendFTPCmd(self, command, input=""):
        self.ftpControlSocket.send(self.buildFTPCmd(command, input))
        return self.ftpControlSocket.recv(1024).decode()

    #Set passive mode.
    def setPassiveMode(self):
        passiveResp = self.sendFTPCmd(self.PASSIVECOMMAND)
        print(passiveResp)
        passivePort = self.getPassivePort(passiveResp)
        return passivePort

    #In FTP the PASV command returns a tuple-like thing.
    #It has, as comma seperated values, the octal components
    #of the server IP and two octal components describing the
    #port that the client needs to connect to.
    #It looks like (192,168,1,1,128,113)
    #To get the port, you do the following with the last two values:
    #(128*256)+113, or, (part1*256)+part2.
    def getPassivePort(self, pasvResp):
        #Getting the section of the response with the values.
        #Probably should just search for the first '('.
        commaString = pasvResp[-20:-3]
        portInfo = commaString.split(",")
        #The value multiplied by 256.
        multiplier = int(portInfo[len(portInfo)-2])
        #The extra bit we add on.
        extraBit = int(portInfo[len(portInfo)-1])
        #Return the port number.
        return (multiplier*256)+extraBit

    #Get passive data.
    def recieveFromFTPDataConn(self, command):
        #Set up our TCP connection to the server.
        ftpDataConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = self.setPassiveMode()
        print("Server assigned port "+str(port))
        ftpDataConnection.connect((self.host, port))
        #Send our intended command via the contol channel.
        self.ftpControlSocket.send(self.buildFTPCmd(self.LISTCOMMAND, ""))
        time.sleep(2)
        #Get the output from the data channel.
        #ftpDataConnection.send("1\n".encode())

        #Ugly bit of code to get all of the data from the server response.
        output = ""
        while 1:
            recv = ftpDataConnection.recv(1024).decode()
            if recv == "":
                break
            output += recv
        
        ftpDataConnection.close()
        return output

    ###############
    #Actual FTP related functions here.
    ###############

    def login(self, userName, password):
        #User Command
        resp = self.sendFTPCmd(self.USERCOMMAND, userName)
        if resp[0:3] == "331":
            print("Server is happy with username.")
        else:
            raise UserCredentialsException(resp+"\nThe server wasn't happy with the username.")
            
        #Pass Command
        resp = self.sendFTPCmd(self.PASSCOMMAND, password)
        if resp[0:3] == "230":
            print("Correct password, the server likes you.")
            print(resp)
        else:
            raise UserCredentialsException(resp+"\nWell, I've helped you all I can, the server didn't like your password.")

    def pwd(self):
        return self.sendFTPCmd(self.PWDCOMMAND)

    def listFiles(self):
        return self.recieveFromFTPDataConn(self.LISTCOMMAND)

    def close(self):
        self.ftpControlSocket.close()

class UserCredentialsException(Exception):
    pass

if __name__ == "__main__":
    main()