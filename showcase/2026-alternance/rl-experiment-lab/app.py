"""Bandit epsilon-greedy reproductible : exploration vs exploitation."""
import random

def simulate(probabilities,steps=1000,epsilon=.1,seed=42):
    if not probabilities or any(not 0<=p<=1 for p in probabilities) or steps<=0 or not 0<=epsilon<=1:
        raise ValueError("Paramètres invalides")
    rng=random.Random(seed);counts=[0]*len(probabilities); successes=[0]*len(probabilities);total=0
    for _ in range(steps):
        best=max(range(len(counts)),key=lambda i:successes[i]/counts[i] if counts[i] else float("inf"))
        index=rng.randrange(len(counts)) if rng.random()<epsilon else best
        reward=int(rng.random()<probabilities[index])
        counts[index]+=1;successes[index]+=reward;total+=reward
    return {"steps":steps,"seed":seed,"counts":counts,"mean_reward":round(total/steps,4)}

def baseline(probabilities,steps=1000,seed=42):
    rng=random.Random(seed)
    return sum(rng.random()<probabilities[rng.randrange(len(probabilities))] for _ in range(steps))/steps

if __name__=="__main__":
    print("epsilon-greedy",simulate([.2,.45,.7],10000))
    print("random",round(baseline([.2,.45,.7],10000),4))
