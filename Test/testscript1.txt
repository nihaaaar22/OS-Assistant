import matplotlib.pyplot as plt
import numpy as np

# Generate a range of x values from 0 to 10
x = np.linspace(0, 10, 1000)

# Calculate the corresponding y values using the formula for a circle
y = np.sqrt(1 - x**2)

# Create a figure and axis
fig, ax = plt.subplots()

# Plot the upper and lower halves of the circle
ax.plot(x, y, label='Upper half')
ax.plot(x, -y, label='Lower half')

# Set the aspect ratio of the plot to be equal so the circle appears as a circle
ax.set_aspect('equal')

# Set the title and labels
ax.set_title('Graphical Representation of Pi')
ax.set_xlabel('x')
ax.set_ylabel('y')

# Add a legend
ax.legend()

# Show the plot
plt.show()