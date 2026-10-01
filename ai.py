# import csv
# file = open("C:\\Users\\STUDENTS\\Desktop\\dhruba\\my.csv", "r")
# details = csv.reader(file)
# for row in details:
#     print(row)

# #sp1
# print("national animal of india is tiger")
# #sp2
# length = 12
# breadth = 7 
# area = length * breadth
# print("area of the rectangle is:", area)

# #Creating a NumPy array using a list of tuples 
# import numpy as np
# arr = np.array([(1, 2, 3, 4, 5), (5, 6, 7, 8, 9)])
# print("numpy array is: \n", arr)

# #Creating a NumPy array using a value from the user using the `empty` function 
# import numpy as np
# n=int(input("Enter the size of the array: "))
# arr = np.empty(n)   
# for i in range(n):
#     arr[i]=int(input("Enter a number: "))
# print("numpy array is: \n", arr)

#Creating a data frame using NumPy ndarray 
import pandas as pd 
import numpy as ny
arr1 = ny.array([10,20,30,])
arr2 = ny.array([100,200,300])
arr3 = ny.array([-10,-20,-30])
df = pd .DataFrame([arr1,arr2,arr3] , columns=[])