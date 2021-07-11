
import numpy as np
import pandas as pd
import json
import subprocess
import os
import plotext as plt
import math
import sys
#import thread
import multiprocessing
import select
import termios
import tty



sensorName = "icm4x6xx Accelerometer Wakeup"
sensorName_2 = "gravity  Wakeup"


def execute(cmd):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True, shell=True)                                 
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def isData():

    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])




def main():

    df = pd.DataFrame({"time":[0],"X":[0],"Y":[0],"Z":[0], "vX":[0],"vY":[0],"vZ":[0], "dX":[0],"dY":[0],"dZ":[0]})
    columns= df.columns
    index =1
    maximum_ylim = 10


 # checm for program parameters
    if (len(sys.argv)>1):
        delayInput = sys.argv[1]
    else:
        delayInput = "100"


    delay = float(delayInput)/1000
    numPoints = int((1/delay)+1)
    jsonStr=""

    #print(sensorName)
    #would you like to read a saved file?

    print("Would you like to read a saved file or read new data? s/c: ")
    readSaved = input()
    if readSaved.lower() == 's' :
        print("\n\n Please enter a file name: ")
        fileName= input()
        df = pd.read_pickle(fileName)
        delay = df["time"].iat[1] - df["time"].iat[0]
        numPoints = int((1/delay)-1)


        maxScroll = len(df.index)-numPoints-1

        Scroll=0

       # while true:
        
        graphData(df[:numPoints],maximum_ylim)

        
        

        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())

            while 1:
        
                    if isData():
                        c = sys.stdin.read(1)

                        if c == 'a' and Scroll>1:
                            Scroll-=1

                        if c == 'l' and Scroll<maxScroll:
                            Scroll+=1
                         #print(c)
                        if c == '\x1b':         # x1b is ESC
                           #  i=0
                            break

                        graphData(df[Scroll: Scroll+numPoints],maximum_ylim)

        
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        

            
        return 0




    # Capturing termux api sensor data using generatir function yeilding api stream by line

    try:


        for path in execute("termux-sensor -s \"icm4x6xx Accelerometer Wakeup\",\"gravity  Wakeup\" -d" + delayInput):

        
            if path != "{}\n":
                jsonStr += path
            
            if path == "}\n" :
                if (jsonStr != "{}"):
                    if not  sensorName_2 in  jsonStr:
                    
                        jsonStr=""
                    else:
                    
                        df=df.append(formatData(jsonStr, df[-1:], delayInput, columns, index))
                        jsonStr=""

                        maximum_ylim = 10
                        absolute = df[["X","Y","Z"]][-10:].abs()
                        for col in absolute.columns:
                            if (maximum_ylim < absolute[col].max()):
                                maximum_ylim = absolute[col].max()
                        index+=1

                       # print(df)
                       #
                        if(index>numPoints):
                            graphData(df[-numPoints:],maximum_ylim)
                        else:
                        
                            graphData(df,maximum_ylim)

                            
                   # print(df)

    # once keyboard exception terminates generator loop
    except:
        print("\n\nReading has been completed.\n")
        print("Would you like to save the data from this session? y/n: ")
        saveConfirmation = input()

        if (saveConfirmation.lower() =='y'):
            print("\n\nPlease enter a file name: ")
            fileName = input()
            df.to_pickle(fileName)
            print("\nFile has been saved! Goodbye")
            

    return 0
            
       # except KeyboardInterrupt:
         #   print('All done')
            # If you actually want the program to exit
      #      raise




def getData(delayInput,index,columns, last):

    #print(last) #index-1

    sensorName = "icm4x6xx Accelerometer Wakeup"
    sensorName_2 = "gravity  Wakeup"


    numberOfPoints = " -n 1"
    termuxSensor = "termux-sensor -s "
    delay= " -d "+ delayInput


    cmd = termuxSensor + "\"" + sensorName + "\"" + ",\"" + sensorName_2 + "\"" + numberOfPoints + delay

    termux_subprocess = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE)
    termux_output = termux_subprocess.stdout.read()

def formatData(termux_output, last, delayInput, columns, index):

    #output_formatted= str(termux_output)[2:-1] #removes bit string quotes
    output_formatted = termux_output.replace("\\n","") #removes new line characters

    data= json.loads(output_formatted) #Returns dictionary from JSON API output

    accel= data[sensorName]["values"] #gets accelerometer vector
    grav= data[sensorName_2]["values"] #gets gravity vector

    #outout is vector subtraction of accel and grav
    output={}
    for x in range(0,3):
        output[columns[x+1]]=accel[x]-grav[x]

        output["v"+columns[x+1]] = integrate(last[columns[x+1]].iat[0],output[columns[x+1]],float(delayInput)/1000)

        output["v"+columns[x+1]] += last["v"+columns[x+1]].iat[0]

        output["d"+columns[x+1]] = integrate(last["v"+columns[x+1]].iat[0],output["v"+columns[x+1]],float(delayInput)/1000)

        output["d"+columns[x+1]] += last["d"+columns[x+1]].iat[0]
    
    time = {"time":float(delayInput)*index/1000}

    return[time |  output]
    


 
def graphData(df,maximum):


    plt.plot(df["time"],df["X"],label= "X")
    plt.plot(df["time"],df["Y"],label= "Y")
    plt.plot(df["time"],df["Z"],label= "Z")


    plt.ylim(-maximum,maximum)
    
    plt.canvas_color("black")
    plt.axes_color("black")
    plt.ticks_color("cloud")
    
    plt.grid(False,False)
    
    plt.title("acceleration vs time")
    plt.xlabel("time (s)")
    plt.ylabel("acceleration (m/s^2)")
    
    plt.figsize(72,32)

    plt.clt()
  #  plt.sleep(0.1)
    plt.show()
    plt.clp()


def integrate(y1, y2, deltaX):

    return deltaX *(y1 + float(y2))/2



class polynomial: #netwon series describing a polynomial

    coefficients =[]

    def init(self,coefficents):
        self.coefficents = coefficents

    def integrate(self):

        degree = len(self.coefficients)
        
        self.coefficients = self.coefficents.append(coefficents/degree)

        for index in range(degree-1,0,-1):
            self.coefficient[index]= self.coefficient[index-1]/index


    def derivative(self):

        degree = len(self.coefficients)

        

       # return 0



   
    

    

    



if __name__ == '__main__':
    main()
