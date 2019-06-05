#This code is used to save the running configuration of your network devices that are listed in the Devices.xlsx file. There is a type column in the excel sheet where one indicates a firewall device and Zero a non-firewall device.

#importing functions.
import pandas as pd
import paramiko, datetime,os, time, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase

#Defining counters.
Suc = 0
Tot = 0

#Defining SSH CERD.
port = 22
username = ''
password = ''
enable_password = '' #this is for the routers and firewalles in case the enable password is needed

#Defining Time, Path to save files, and Excel sheet path.
now = datetime.datetime.today().strftime('%Y-%m-%d')
path = 'E:/Backup/Running configuration'  #The path where the files will be stored
path = path + "/Runningconfig_" +str(now)  #The folder of the backup files with the backup date
excel_file = "E:/Backup/APP/Devices/DevicesAll.xlsx" #Full path of the excel sheet

#Creating the Directory if it doesn't exist.
if not os.path.isdir(path):
    os.mkdir(path)

#Reading Excel sheet content.
Device = pd.read_excel(excel_file)

#Loop each row in the excel sheet taking the name of the device and it's IP address to estalish a SSH session to take it's Show run.
for i in Device.index:
    nowdetail = datetime.datetime.today().strftime('%Y-%m-%d:%H:%m')
    try:
        Tot = Tot +1
        DeviceName = Device['Device Name'][i]
        Filename = path + '/' + str(DeviceName) + '_' +str(now) +'.txt'
        Unreachable = path + '/Unreachable' + '_' +str(now) +'.txt'
        Logs = path + '/Logs' + '_' +str(now) +'.txt'
        hostname = str(Device['IP Address'][i])
        DeviceType = Device['Type'][i]
        
        #For Non-firewall devices
        if DeviceType == 0:
            #Strating the ssh session
            s = paramiko.SSHClient()
            s.load_system_host_keys()
            s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            s.connect(hostname, port, username, password)


            #Executing the show run command.
            command = 'show running-config'
            (stdin, stdout, stderr) = s.exec_command(command)
        
            #opening and writing in to a file the show run
            file = open(Filename,'w')
            for line in stdout.readlines():
                file.write(str(line))
            file.close()
        
        #For Firewall devices
        elif DeviceType == 1:
            
            client_pre=paramiko.SSHClient()
            client_pre.load_system_host_keys()
            client_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client_pre.connect(hostname, username=username , password=password, look_for_keys=False, allow_agent=False)

            client=client_pre.invoke_shell()
            time.sleep(2)
            output=client.recv(65535)

            client.send('enable\n')
            time.sleep(2)
            output=client.recv(65535)

            client.send(enable_password + '\n')
            time.sleep(2)
            output=client.recv(65535)

            client.send('terminal pager 0\n')
            time.sleep(2)
            output=client.recv(65535)

            client.send('more system:run\n')
            time.sleep(5)
            run = ""
            output = " "

            while client.recv_ready():
             output = client.recv(65535)
             run += output.decode('UTF-8');

            #print (version_info)
            client.close()
            client_pre.close()
            #opening and writing in to a file the show run
            file = open(Filename,'w')
            file.write(str(run))
            file.close()
        #printing device name in the terminal.
        print(DeviceName)
        Suc = Suc + 1
    except OSError:
        fileU = open(Unreachable,'a')
        inp = str(DeviceName) + '_' +str(nowdetail) + '\n'
        fileU.write(str(inp))
        fileU.close()
        fileU = open(Logs,'a')
        fileU.write(str(OSError))
        fileU.close()
    except  paramiko.AuthenticationException:
        fileU = open(Unreachable,'a')
        inp = str(DeviceName) + '_' +str(nowdetail) + '\n'
        fileU.write(str(inp))
        fileU.close()
        output = str(DeviceName) + '\t' +str(nowdetail) + 'Authentication Failed' + '\n'
        fileU = open(Logs,'a')
        fileU.write(str(output))
        fileU.close()

    except  paramiko.SSHException:
        fileU = open(Unreachable,'a')
        inp = str(DeviceName) + '_' +str(nowdetail) + '\n'
        fileU.write(str(inp))
        fileU.close()
        output = str(DeviceName) + '\t' +str(nowdetail) + 'Issues with SSH service' + '\n'
        fileU = open(Logs,'a')
        fileU.write(str(output))
        fileU.close()

    except  socket.error:
        fileU = open(Unreachable,'a')
        inp = str(DeviceName) + '_' +str(nowdetail) + '\n'
        fileU.write(str(inp))
        fileU.close()
        fileU = open(Logs,'a')
        output = str(DeviceName) + '\t' +str(nowdetail) + 'Connection Error' +'\n'
        fileU.write(str(output))
        fileU.close()

unreachable = ''
if not Suc == Tot:
    fileU = open(Unreachable,'r')
    unreach = fileU.read()
    unreachable = ' And the unreachable devices are: \n \n' + str(unreach)

msg = MIMEMultipart()
msg['From'] = 'Network Devices Backup Agent'
msg['To'] = 'Set any name to be dispalyed in the Email'
msg['Subject'] = 'Running Configuration Backup Report'
body = 'Dear Team \n \n This is to inform you that '+ str(Suc) + '  out of ' + str(Tot) +'  network devices has been successfully backed up.' + unreachable +' \n \n The backed up configuration and list of unreachable devices can be found in the following path E:/Backup/Running configuration/Runningconfig' + '_' +str(now) +' \n \n Best regards \n \n Backup Agent'
body = MIMEText(body) # convert the body to a MIME compatible string
msg.attach(body) # attach it to the main message


server = smtplib.SMTP('mail.almadar.ly', 25)
server.starttls()
server.login("Username", "Password") #The username and password of the smtp server (in case it's needed)
server.sendmail('Sender Email address','To emeil address',msg.as_string())
server.quit()
exit()  



