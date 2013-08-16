#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Genetic Algorithme

@author: Olivier BLIN
"""

import array
import random
import csv
from deap import creator, base, tools, algorithms
import multiprocessing

from server_pool import PoolManager

FORMANT_A = 405
FORMANT_B = 2080

IND_SIZE = 16
POP_SIZE = 2

NB_GEN = 4
CXPB = 0.5
MUTPB = 0.2

# Optimization fonction
def evaluate(individual):
    formant_a = sum(individual[0:8])
    formant_b = sum(individual[8:IND_SIZE])

    valA = abs(FORMANT_A - formant_a)
    valB = abs(FORMANT_B - formant_b)

    return valA, valB

def praat_evaluate(a_b):
    formant_a = a_b[0]
    formant_b = a_b[1]

    valA = abs(FORMANT_A - formant_a)
    valB = abs(FORMANT_B - formant_b)

    return valA, valB

def fitness_calc(ind_list):

    print "Individual to evaluate : %i" % len(ind_list)

    if len(ind_list) == 0:
        return list() 

    pool = PoolManager(ind_list)
    res = pool.run()

    fitness = map(praat_evaluate, res)

    # for elem in fitness:
    #     print elem

    return fitness


def genetic_algo():
    # ------------------------------
    # INIT

    # Type
    creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
    creator.create("Individual", list, fitness=creator.FitnessMin)


    # Initialization
    toolbox = base.Toolbox()
    toolbox.register("attr_float", random.random)
    toolbox.register("individual", tools.initRepeat, creator.Individual,
                     toolbox.attr_float, n=IND_SIZE)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # Operators
    toolbox.register("mate", tools.cxTwoPoints)
    toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.1)
    toolbox.register("select", tools.selTournament, tournsize=3)
    # toolbox.register("evaluate", evaluate)

    # # multiproc
    # pool = multiprocessing.Pool()
    # toolbox.register("map", pool.map)

    csvfile = open('glance.csv', 'wb')
    spamwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)

    # ------------------------------
    # ALGO
    pop = toolbox.population(n=POP_SIZE)
    # algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=NB_GEN)

    for g in range(NB_GEN):
        print "Start generation %i" % (g+1)
        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = map(toolbox.clone, offspring)

        # Apply crossover on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CXPB:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

        # Apply mutation on the offspring
        for mutant in offspring:
            if random.random() < MUTPB:
                toolbox.mutate(mutant)
                del mutant.fitness.values

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]

        # fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        fitnesses = fitness_calc(invalid_ind)

        if len(fitnesses) > 0:
            r_elem_pos = random.randrange(0, len(fitnesses))
            r_elem = fitnesses[r_elem_pos]
            spamwriter.writerow([str(g+1), str(r_elem[0]), str(r_elem[1])])
            csvfile.flush()

        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # The population is entirely replaced by the offspring
        pop[:] = offspring

        print "--------------------"

    csvfile.close()

    return pop


if __name__ == "__main__":

    res = genetic_algo()

    for elem in res:
        print evaluate(elem)

    
    



