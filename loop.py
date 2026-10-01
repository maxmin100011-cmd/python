# i = 1 
# while i <= 5:
#     print(i) # Print the current value of i
#     i += 1
#     print(i) # Print the updated value of i

# j = 5
# while j >= 1:
#     print('Current value of j:', j) # Print the current value of j
#     j -= 1
#     # print('Updated value of j:', j) # Print the updated value of j
     
# for i in range(1, 11):
#     if i == 6:
#         break  # Exit the loop when i is 6
#     print('Current value of i:', i , end=" ") # Print the current value of i

# for j in range(1, 11):
#     if j == 6:
# #         continue  # Skip the rest of the loop when j is 6
# #     print('Current value of j:', j , end=" " , sep="\n") # Print the current value of j
# nums = list(range(1, 11))
# target = 100
# for num in nums:
#     if num == target:
#         print(f"Found the target number: {num}")
#         break  # Exit the loop when the target is found
#     print(f"Current number: {num}")
# else:
#     print("Target number not found in the list.")
for i in range(1, 11):
    if i % 2 == 0:
        continue  # Skip even numbers
    print(f"Current odd number: {i}")