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

# Attribut nomber for one personne
IND_SIZE = 8
# crossover proba
CXPB = 0.5 # 0.5
# mutation proba
MUTPB = 0.2 # 0.2

# PERSO
MUTADD = 0.5
MUTRAND = 0.1
# random fonction accuracy or list len
RANDOM_ACCURACY = 0.01


POP_SIZE = 2000
NB_GEN = 30

# keep on each round
ELITE_PERCENT = 15

# Optimization fonction
def evaluate(individual):
    formant_a = sum(individual[0:8])
    formant_b = sum(individual[8:16])

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

    new_list = list()
    for ind in ind_list:
        if len(ind) == 8:
            elem = list()
            for i in range(16):
                elem.append(ind[i/2])
            new_list.append(elem)
        elif len(ind) < 16:
            print "size error"
            new_list.append([0.5]*16)
        else:
            new_list.append(ind)

    pool = PoolManager(new_list)
    res = pool.run()

    fitness = map(praat_evaluate, res)

    # # TEST FUNCTION
    # fitness = list()
    # for ind in new_list:
    #     fitness.append(evaluate(ind))

    return fitness


def affiche(listt):
    for elem in listt:
        print ">",elem

def drange(start, stop, step=1, roundp=1000):
    l = list()
    partnbr = int((stop-start)/step)
    for mult in range(partnbr):
        res = start +(step*mult)
        res = round(res*roundp)/roundp
        if res < stop:
            l.append(res)
    l.append(stop)
    return l

def myrandom():
    if 'LIST_R' not in globals():
        global LIST_R
        LIST_R = drange(0, 1, RANDOM_ACCURACY)
    return random.choice(LIST_R)


def genetic_algo():
    # ------------------------------
    # INIT

    # Type
    creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
    creator.create("Individual", list, fitness=creator.FitnessMin)


    # Initialization
    toolbox = base.Toolbox()
    toolbox.register("attr_float", myrandom)
    toolbox.register("individual", tools.initRepeat, creator.Individual,
                     toolbox.attr_float, n=IND_SIZE)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # Operators
    toolbox.register("mate", tools.cxTwoPoints)
    toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.1)
    toolbox.register("select", tools.selTournament, tournsize=3)
    # toolbox.register("select", tools.selBest)
    # toolbox.register("evaluate", evaluate)

    # # multiproc
    # pool = multiprocessing.Pool()
    # toolbox.register("map", pool.map)

    csvfile = open('glance.csv', 'wb')
    spamwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(["N", "A", "B", "Average","Error"])

    # ------------------------------
    # ALGO
    pop = toolbox.population(n=POP_SIZE)
    elit = []
    # algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=NB_GEN)

    for g in range(NB_GEN):
        print "Start generation %i" % (g+1)
        # Select the next generation individuals
        offspring = toolbox.select(pop, POP_SIZE)
        # offspring = tools.selNSGA2(pop, POP_SIZE)
        

        # Clone the selected individuals
        offspring = map(toolbox.clone, offspring)


        # Apply crossover on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CXPB:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

        # # Apply mutation on the offspring
        # for mutant in offspring:
        #     if random.random() < MUTPB:
        #         toolbox.mutate(mutant)
        #         del mutant.fitness.values

        # Apply mutation on the offspring PERSO
        for mutant in offspring:
            if random.random() < MUTRAND:
                ok = False
                for n in range(len(mutant)):
                    if random.random() < 1/(len(mutant)*1.0):
                        mutant[n] = myrandom()
                        ok = True
                if ok:
                    del mutant.fitness.values

        for mutant in offspring:
            if random.random() < MUTADD:
                ok = False
                for n in range(len(mutant)):
                    if random.random() < 1/(len(mutant)*1.0)/2:
                        mutant[n] += random.choice(map(lambda x: x/100.0 ,range(1, 10)))
                        ok = True
                    elif random.random() < 1/(len(mutant)*1.0)/2:
                        mutant[n] -= random.choice(map(lambda x: x/100.0 ,range(1, 10)))
                        ok = True

                    mutant[n] = round(mutant[n]*100)/100
                    if mutant[n] > 1 or mutant[n] < 0:
                        mutant[n] = myrandom()
                if ok:
                    del mutant.fitness.values

        # Apply crossover and mutation on the offspring
        # offspring = algorithms.varAnd(offspring, toolbox, CXPB, MUTPB)

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]

        # fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        fitnesses = fitness_calc(invalid_ind)


        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # The population is entirely replaced by the offspring
        pop[:] = offspring + elit

        # Save average evolution
        try:
            sum_a = 0
            sum_b = 0
            nb = 0
            for elem in pop:
                val = elem.fitness.values
                if val[0] != 0 and val[1] != 0:
                    nb += 1
                    sum_a += val[0]
                    sum_b += val[1]

            spamwriter.writerow([str(g+1), str(sum_a/nb), str(sum_b/nb), str((sum_a+sum_b)/nb/2), str(len(pop)-nb)])
            csvfile.flush()
        except Exception:
            pass


        try:
            resss = min(pop, key = lambda elem: (elem.fitness.values[0]+elem.fitness.values[1])/2)

            print "Min :", resss.fitness.values
        except Exception:
            pass

        try:
            elit = sorted(pop, key = lambda elem: (elem.fitness.values[0]+elem.fitness.values[1])/2)[:(POP_SIZE/ELITE_PERCENT)]
        except Exception as e:
            elit = []

        # min(e, key = lambda t: (t[0]+t[1])/2)

        print "--------------------"

    csvfile.close()

    return pop


if __name__ == "__main__":

    res = genetic_algo()

    for elem in res:
        print evaluate(elem)

    
    



