import math
import copy
import matplotlib.pyplot as plt

# Discount factor and convergence tolerance from the assignment setup
disc = 0.99
tol = 1e-6

# direction = ["up", "down", "left", "right"]

# The four actions the agent can choose from in each state
moves = ["U", "D", "L", "R"]

# Row/column change caused by each action
deltas = {
    "U": (-1, 0),
    "D": (1, 0),
    "L": (0, -1),
    "R": (0, 1),
}

# If the intended action fails, the agent slips to one of the two perpendicular directions
perp = {
    "U": ["L", "R"],
    "D": ["L", "R"],
    "L": ["U", "D"],
    "R": ["U", "D"],
}

# Just for nicer policy printing
symbols = {
    "U": "↑",
    "D": "↓",
    "L": "←",
    "R": "→",
}


class MazeWorld:
    def __init__(self, grid, start=None):
        # Store the maze layout and basic dimensions
        self.grid = grid
        self.nrows = len(grid)
        self.ncols = len(grid[0])
        self.start = start

        # Collect all valid non-wall cells once, so we can iterate over states easily later
        self.cells = []
        for i in range(self.nrows):
            for j in range(self.ncols):
                if grid[i][j] is not None:
                    self.cells.append((i, j))

    def in_bounds(self, i, j):
        # A cell is valid if it is inside the maze and not a wall
        return 0 <= i < self.nrows and 0 <= j < self.ncols and self.grid[i][j] is not None

    def get_reward(self, cell):
        # Reward of the current state
        i, j = cell
        return self.grid[i][j]





    def step(self, cell, direction):
        # Try to move in the requested direction
        # If that move hits a wall or boundary, stay in the same cell
        i, j = cell
        di, dj = deltas[direction]
        ni, nj = i + di, j + dj
        if self.in_bounds(ni, nj):
            return (ni, nj)
        return cell

    def outcomes(self, cell, direction):
        # Transition model:
        # 0.8 -> intended direction
        # 0.1 -> one perpendicular direction
        # 0.1 -> the other perpendicular direction
        #
        # Some outcomes may end up in the same destination state
        # (for example, if multiple moves are blocked), so probabilities are merged.
        result = {}
        weighted = [(0.8, direction), (0.1, perp[direction][0]), (0.1, perp[direction][1])]
        for p, d in weighted:
            dest = self.step(cell, d)
            result[dest] = result.get(dest, 0.0) + p
        return list(result.items())


def blank_vals(world):
    # Start with utility 0 for every non-wall state
    return {c: 0.0 for c in world.cells}
'''
def blank_policy(world):
    # return 0 for a non wall square?
'''
def action_score(world, cell, direction, V):
    # Expected utility of taking one action from one state
    total = 0.0
    for dest, p in world.outcomes(cell, direction):
        total += p * V[dest]
    return total


def greedy(world, cell, V):
    # Pick the action with the highest expected utility under the current value function
    top_dir = None
    top_val = -math.inf
    for d in moves:
        v = action_score(world, cell, d, V)
        if v > top_val:
            top_val = v
            top_dir = d
    return top_dir, top_val


def derive_policy(world, V):
    # Turn a value function into a policy by choosing the best action in each state
    pi = {}
    for c in world.cells:
        best, _ = greedy(world, c, V)
        pi[c] = best
    return pi


def show_vals(world, V, dp=3):
    # Pretty-print the utility of each cell in grid form
    print("\nUtilities:")
    for i in range(world.nrows):
        line = []
        for j in range(world.ncols):
            if world.grid[i][j] is None:
                line.append("#####".rjust(8))
            else:
                line.append(f"{V[(i, j)]:.{dp}f}".rjust(8))
        print(" ".join(line))


def show_policy(world, pi):
    # Pretty-print the policy in grid form using arrows
    print("\nPolicy:")
    for i in range(world.nrows):
        line = []
        for j in range(world.ncols):
            if world.grid[i][j] is None:
                line.append("  #  ")
            else:
                line.append(f"  {symbols[pi[(i, j)]]}  ")
        print(" ".join(line))


def plot_vals(snapshots, watch, heading):
    # Plot how selected state utilities change over iterations
    xs = list(range(len(snapshots)))
    plt.figure(figsize=(10, 6))
    for c in watch:
        ys = [snap[c] for snap in snapshots]
        plt.plot(xs, ys, label=f"State {c}")
    plt.xlabel("Iteration")
    plt.ylabel("Utility estimate")
    plt.title(heading)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

"""
def plot_policy_changes(world, log_pi, watch, heading):
    xs = list(range(len(log_pi)))
    plt.figure(figsize=(10, 6))
    for c in watch:
        ys = [log_pi[i][c] for i in range(len(log_pi))]
        plt.plot(xs, ys, label=f"State {c}")
    plt.xlabel("Iteration")
    plt.ylabel("Action (encoded as integer)")
    plt.title(heading)
    plt.yticks(ticks=range(len(moves)), labels=[symbols[d] for d in moves])
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
"""

def compare(world, V1, pi1, h1, V2, pi2, h2, thresh=1e-4):
    # Compare the final outputs of value iteration and policy iteration
    print("\nCompare PI and VI")

    match = True
    for c in world.cells:
        if pi1[c] != pi2[c]:
            match = False
            print(f"Policy mismatch at {c}: VI={pi1[c]}, PI={pi2[c]}")
    print("Policies identical?", match)

    worst = 0.0
    close = True
    for c in world.cells:
        gap = abs(V1[c] - V2[c])
        worst = max(worst, gap)
        if gap > thresh:
            close = False
            print(f"Utility mismatch at {c}: VI={V1[c]:.6f}, PI={V2[c]:.6f}, diff={gap:.6f}")

    print("Utilities close?", close)
    print("Maximum utility difference:", worst)
    print("Value iteration iterations:", len(h1) - 1)
    print("Policy iteration outer iterations:", len(h2))


def value_iteration(world, gamma=disc, eps=tol):
    # Standard Bellman optimality updates until convergence
    V = blank_vals(world)
    log = [copy.deepcopy(V)]

    while True:
        V2 = {}
        biggest = 0.0

        # Update every state using the previous iteration's values
        for c in world.cells:
            _, fut = greedy(world, c, V)
            V2[c] = world.get_reward(c) + gamma * fut
            biggest = max(biggest, abs(V2[c] - V[c]))

        V = V2
        log.append(copy.deepcopy(V))

        # Stop when the largest utility change is small enough
        if biggest < eps * (1 - gamma) / gamma:
            break

    return V, derive_policy(world, V), log


def eval_policy(world, pi, gamma=disc, eps=tol):
    # Evaluate one fixed policy until the utilities stabilize
    V = blank_vals(world)

    while True:
        V2 = {}
        biggest = 0.0

        for c in world.cells:
            # Here we do not maximize over actions;
            # we only follow the action prescribed by the current policy
            fut = sum(p * V[d] for d, p in world.outcomes(c, pi[c]))
            V2[c] = world.get_reward(c) + gamma * fut
            biggest = max(biggest, abs(V2[c] - V[c]))

        V = V2
        if biggest < eps * (1 - gamma) / gamma:
            break

    return V
"""
def policy_iteration(world, gamma=disc, eps=tol):
   
    # pi = False
    pi = {c: "U" for c in world.cells}
    log = []

    while True:
        
        V = eval_policy(world, pi, gamma, eps)
"""
def policy_iteration(world, gamma=disc, eps=tol):
    # Start with any simple policy; "always go up" is fine
    pi = {c: "U" for c in world.cells}
    log = []

    while True:
        # First evaluate the current policy
        V = eval_policy(world, pi, gamma, eps)
        log.append(copy.deepcopy(V))

        # Then improve it greedily with respect to the current utilities
        changed = False
        new_pi = {}

        for c in world.cells:
            old = pi[c]
            best, _ = greedy(world, c, V)
            new_pi[c] = best
            if best != old:
                changed = True

        pi = new_pi

        # If nothing changed, the policy is stable and we can stop
        if not changed:
            break

    return V, pi, log


def build_grid():
    # Maze from the assignment figure:
    # white = -0.05, green = +1, brown = -1, wall = None
    layout = [
        [ 1.0,   None,  1.0,  -0.05, -0.05,  1.0],
        [-0.05, -1.0,  -0.05,  1.0,   None, -1.0],
        [-0.05, -0.05, -1.0,  -0.05,  1.0,  -0.05],
        [-0.05, -0.05, -0.05, -1.0,  -0.05,  1.0],
        [-0.05,  None,  None,   None, -1.0,  -0.05],
        [-0.05, -0.05, -0.05, -0.05, -0.05, -0.05],
    ]
    return layout, (3, 2)

def build_custom_grid():
    layout = [
        [-0.05, -0.05, -0.05,  1.0,   None,  -0.05, -0.05,  1.0],
        [-0.05,  None,  -1.0, -0.05,  None,  -0.05, -1.0,  -0.05],
        [-0.05, -0.05, -0.05, -0.05, -0.05, -0.05, -0.05, -0.05],
        [ 1.0,   None,  -0.05,  None, -1.0,   None, -0.05, -0.05],
        [-0.05, -0.05, -0.05, -0.05, -0.05, -0.05,  None,  1.0],
        [-1.0,   None,   None, -0.05,  None, -0.05, -0.05, -0.05],
        [-0.05, -0.05, -0.05, -1.0,  -0.05, -0.05,  None, -0.05],
        [-0.05,  1.0,   -0.05, -0.05, -0.05, -1.0,  -0.05, -0.05],
    ]
    start = (7, 0)
    return layout, start

def main():
    
    layout, start = build_grid()
    world = MazeWorld(layout, start=start)

    # A few representative states to track in the convergence plots
    watch = [start, (0, 0), (1, 1), (5, 5)]

    print("Part 1, VI")
    V_vi, pi_vi, log_vi = value_iteration(world)
    show_vals(world, V_vi)
    show_policy(world, pi_vi)
    print(f"\nStart state: {start}")
    print(f"Start utility (VI): {V_vi[start]:.6f}")
    print(f"Best action from start (VI): {pi_vi[start]}")
    plot_vals(log_vi, watch, "Value Iteration: Utility estimates over iterations")

    print("\nPart 1, PI")
    V_pi, pi_pi, log_pi = policy_iteration(world)
    show_vals(world, V_pi)
    show_policy(world, pi_pi)
    print(f"\nStart utility (PI): {V_pi[start]:.6f}")
    print(f"Best action from start (PI): {pi_pi[start]}")
    plot_vals(log_pi, watch, "Policy Iteration: Utility estimates over outer iterations")

    compare(world, V_vi, pi_vi, log_vi, V_pi, pi_pi, log_pi)
    
    layout2, start2 = build_custom_grid()
    world2 = MazeWorld(layout2, start=start2)

    # Track a few representative states for the new maze
    watch2 = [start2, (0, 3), (3, 0), (7, 1)]

    print("\nPart 2: VI")
    V_vi2, pi_vi2, log_vi2 = value_iteration(world2)
    show_vals(world2, V_vi2)
    show_policy(world2, pi_vi2)
    print(f"\nStart state: {start2}")
    print(f"Start utility (VI): {V_vi2[start2]:.6f}")
    print(f"Best action from start (VI): {pi_vi2[start2]}")
    plot_vals(log_vi2, watch2, "Part 2 - Value Iteration: Utility estimates over iterations")

    print("\nPart 2: PI")
    V_pi2, pi_pi2, log_pi2 = policy_iteration(world2)
    show_vals(world2, V_pi2)
    show_policy(world2, pi_pi2)
    print(f"\nStart utility (PI): {V_pi2[start2]:.6f}")
    print(f"Best action from start (PI): {pi_pi2[start2]}")
    plot_vals(log_pi2, watch2, "Part 2 - Policy Iteration: Utility estimates over outer iterations")

    compare(world2, V_vi2, pi_vi2, log_vi2, V_pi2, pi_pi2, log_pi2)

    # Simple summary for Part 2 discussion
    print("\nPart 2 summary")
    print(f"Number of non-wall states in custom maze: {len(world2.cells)}")
    print(f"Value iteration iterations: {len(log_vi2) - 1}")
    print(f"Policy iteration outer iterations: {len(log_pi2)}")


if __name__ == "__main__":
    main()