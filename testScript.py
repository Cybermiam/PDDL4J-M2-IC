from matplotlib import pyplot as plt
import re
import subprocess
import os
# Define the commands and problems
commands = {
    "SAT4JPlanner": "java -cp \"classes;lib/pddl4j-4.0.0.jar;lib/org.sat4j.core.jar\" fr.uga.pddl4j.examples.asp.SAT4JPlanner",
    "HSP": "java -cp \"classes;lib/pddl4j-4.0.0.jar;lib/org.sat4j.core.jar\" fr.uga.pddl4j.examples.asp.HSP"
}
domains = ["logistics", "blocks", "gripper", "depots"]
problems = []

for domain in domains:
    for i in range(1, 11):
        problems.append((f"pddl/{domain}/domain/domain.pddl", f"pddl/{domain}/problems/p{i:02}.pddl"))

# Function to execute a command and capture the output
def execute_command(command, timeout=300):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout
    except subprocess.TimeoutExpired:
        return "TimeoutExpired"
# Function to parse the output and extract relevant data
def parse_output(output):
    if output == "TimeoutExpired":
        return float('inf'), 0
        # Regex pattern to capture x and y
    patern = r"\|(\d+)\|(\d+)\|"

    # Find matches
    match = re.search(patern, output)

    if match:
        time_spent = match.group(1)
        steps = int(match.group(2))
        print(f"time_spent: {time_spent}, steps: {steps}")
        if time_spent:
            time_spent = float(time_spent) / 1000  # Convert ms to seconds
        else:
            time_spent = 0.0
        return time_spent, steps

# Data storage
results = []

# Execute commands for each problem and store results
for problem in problems:
    domain, problem_file = problem
    for solver, command in commands.items():
        full_command = f"{command} {domain} {problem_file}"
        print(f"Executing: {full_command}")
        output = execute_command(full_command)
        time_spent, steps = parse_output(output)
        results.append((solver, problem_file, time_spent, steps))


# Create xplot directory if it doesn't exist
if not os.path.exists("xplot"):
    os.makedirs("xplot")


# Function to calculate scores
def calculate_scores(results, domains, commands):
    scores = {solver: {domain: 0 for domain in domains} for solver in commands.keys()}
    for domain in domains:
        domain_results = [result for result in results if domain in result[1]]
        for i in range(1, 11):
            problem_results = [result for result in domain_results if f"p{i:02}" in result[1]]
            if len(problem_results) == 2:
                solver1, solver2 = problem_results
                time1, steps1 = solver1[2], solver1[3]
                time2, steps2 = solver2[2], solver2[3]
                if time1 == float('inf') and time2 == float('inf'):
                    continue
                elif time1 == float('inf'):
                    scores[solver2[0]][domain] += 2
                elif time2 == float('inf'):
                    scores[solver1[0]][domain] += 2
                else:
                    if time1 < time2:
                        scores[solver1[0]][domain] += 1
                        scores[solver2[0]][domain] += time1 / time2
                    else:
                        scores[solver2[0]][domain] += 1
                        scores[solver1[0]][domain] += time2 / time1
                    if steps1 < steps2:
                        scores[solver1[0]][domain] += 1
                        scores[solver2[0]][domain] += steps1 / steps2
                    else:
                        scores[solver2[0]][domain] += 1
                        scores[solver1[0]][domain] += steps2 / steps1
    return scores

# Generate Markdown file
with open("SATResults10Problems.md", "w") as md_file:
    md_file.write("# Comparison of SAT4JPlanner and HSP\n\n")
    md_file.write("| Solver | Problem | Time Spent (s) | Steps |\n")
    md_file.write("|--------|---------|----------------|-------|\n")
    for result in results:
        md_file.write(f"| {result[0]} | {result[1]} | {result[2]:.2f} | {result[3]} |\n")

    # Calculate scores
    scores = calculate_scores(results, domains, commands)

    # Generate domain-specific plots for steps and time
    for domain in domains:
        domain_times = {solver: sum(result[2] for result in results if result[0] == solver and domain in result[1]) for solver in commands.keys()}
        domain_steps = {solver: sum(result[3] for result in results if result[0] == solver and domain in result[1]) for solver in commands.keys()}

        # Plot domain-specific total time
        plt.figure(figsize=(10, 5))
        plt.title(f"Total Time for {domain.capitalize()}")
        plt.bar(commands.keys(), [domain_times[solver] for solver in commands.keys()], color=['blue', 'orange'])
        plt.ylabel('Time (s)')
        domain_time_plot_filename = f"xplot/{domain}_total_time.png"
        plt.savefig(domain_time_plot_filename)
        plt.close()

        # Plot domain-specific total steps
        plt.figure(figsize=(10, 5))
        plt.title(f"Total Steps for {domain.capitalize()}")
        plt.bar(commands.keys(), [domain_steps[solver] for solver in commands.keys()], color=['blue', 'orange'])
        plt.ylabel('Steps')
        domain_steps_plot_filename = f"xplot/{domain}_total_steps.png"
        plt.savefig(domain_steps_plot_filename)
        plt.close()

        #plot domain-specific scores
        plt.figure(figsize=(10, 5))
        plt.title(f"Scores for {domain.capitalize()}")
        plt.bar(commands.keys(), [scores[solver][domain] for solver in commands.keys()], color=['blue', 'orange'])
        plt.ylabel('Score')
        domain_scores_plot_filename = f"xplot/{domain}_scores.png"
        plt.savefig(domain_scores_plot_filename)
        plt.close()

        # Include domain-specific plots in Markdown file
        md_file.write(f"## {domain.capitalize()} Results\n\n")
        md_file.write(f"![Scores for {domain.capitalize()}]({domain_scores_plot_filename})\n")
        md_file.write(f"![Total Time for {domain.capitalize()}]({domain_time_plot_filename})\n")
        md_file.write(f"![Total Steps for {domain.capitalize()}]({domain_steps_plot_filename})\n")

    # Overall results
    overall_scores = {solver: sum(scores[solver][domain] for domain in domains) for solver in commands.keys()}
    overall_steps = {solver: sum(result[3] for result in results if result[0] == solver) for solver in commands.keys()}
    overall_time = {solver: sum(result[2] for result in results if result[0] == solver) for solver in commands.keys()}

    # Plot overall total time
    plt.figure(figsize=(10, 5))
    plt.title("Overall Total Time")
    plt.bar(commands.keys(), [overall_time[solver] for solver in commands.keys()], color=['blue', 'orange'])
    plt.ylabel('Time (s)')
    overall_time_plot_filename = "xplot/overall_total_time.png"
    plt.savefig(overall_time_plot_filename)
    plt.close()

    # Plot overall total steps
    plt.figure(figsize=(10, 5))
    plt.title("Overall Total Steps")
    plt.bar(commands.keys(), [overall_steps[solver] for solver in commands.keys()], color=['blue', 'orange'])
    plt.ylabel('Steps')
    overall_steps_plot_filename = "xplot/overall_total_steps.png"
    plt.savefig(overall_steps_plot_filename)
    plt.close()

    # Plot overall scores
    plt.figure(figsize=(10, 5))
    plt.title("Overall Scores")
    plt.bar(commands.keys(), [overall_scores[solver] for solver in commands.keys()], color=['blue', 'orange'])
    plt.ylabel('Score')
    overall_scores_plot_filename = "xplot/overall_scores.png"
    plt.savefig(overall_scores_plot_filename)
    plt.close()

    # Include overall plots in Markdown file
    md_file.write("## Overall Results\n\n")
    md_file.write(f"![Overall Total Time]({overall_time_plot_filename})\n")
    md_file.write(f"![Overall Total Steps]({overall_steps_plot_filename})\n")
    md_file.write(f"![Overall Scores]({overall_scores_plot_filename})\n")

    