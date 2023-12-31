
from typing import List, Dict, Callable, Iterable

import GDforPSO
from torch_pso.optim.GenericPSO import clone_param_group, clone_param_groups, _initialize_param_groups, GenericParticle,GenericPSO
import torch






class Particle(GenericParticle):
    r"""
    Algorithm from Wikipedia: https://en.wikipedia.org/wiki/Particle_swarm_optimization
    Let S be the number of particles in the swarm, each having a position xi ∈ ℝn in the search-space
    and a velocity vi ∈ ℝn. Let pi be the best known position of particle i and let g be the best known
    position of the entire swarm.
    The values blo and bup represent the lower and upper boundaries of the search-space respectively.
    The w parameter is the inertia weight. The parameters φp and φg are often called cognitive coefficient and
    social coefficient.

    The termination criterion can be the number of iterations performed, or a solution where the adequate
    objective function value is found. The parameters w, φp, and φg are selected by the practitioner and control
    the behaviour and efficacy of the PSO method.

    for each particle i = 1, ..., S do
        Initialize the particle's position with a uniformly distributed random vector: xi ~ U(blo, bup)
        Initialize the particle's best known position to its initial position: pi ← xi
        if f(pi) < f(g) then
            update the swarm's best known position: g ← pi
        Initialize the particle's velocity: vi ~ U(-|bup-blo|, |bup-blo|)
    while a termination criterion is not met do:
        for each particle i = 1, ..., S do
            for each dimension d = 1, ..., n do
                Pick random numbers: rp, rg ~ U(0,1)
                Update the particle's velocity: vi,d ← w vi,d + φp rp (pi,d-xi,d) + φg rg (gd-xi,d)
            Update the particle's position: xi ← xi + vi
            if f(xi) < f(pi) then
                Update the particle's best known position: pi ← xi
                if f(pi) < f(g) then
                    Update the swarm's best known position: g ← pi


    :param param_groups: list of dict containing parameters
    :param inertial_weight: float representing inertial weight of the particles
    :param cognitive_coefficient: float representing cognitive coefficient of the particles
    :param social_coefficient: float representing social coefficient of the particles
    :param max_param_value: Maximum value of the parameters in the search space
    :param min_param_value: Minimum value of the parameters in the search space
    """

    def __init__(self,
                 param_groups: List[Dict],
                 inertial_weight: float,
                 cognitive_coefficient: float,
                 social_coefficient: float,
                 model: float,
                 max_param_value: float = 10.,
                 min_param_value: float = -10,
                 ):
        magnitude = abs(max_param_value - min_param_value)
        self.param_groups = param_groups
        self.position = _initialize_param_groups(param_groups, max_param_value, min_param_value)
        self.velocity = _initialize_param_groups(param_groups, magnitude, -magnitude)
        self.best_known_position = clone_param_groups(self.position)
        self.best_known_loss_value = torch.inf
        self.listOfModelParameters = model
        self.inertial_weight = inertial_weight
        self.cognitive_coefficient = cognitive_coefficient
        self.social_coefficient = social_coefficient

    def step(self, closure: Callable[[], torch.Tensor], global_best_param_groups: List[Dict]) -> torch.Tensor:
        """
        Particle will take one step.
        :param closure: A callable that reevaluates the model and returns the loss.
        :param global_best_param_groups: List of param_groups that yield the best found loss globally
        :return:
        """



        testPos = self.position[0]['params']
        testGlob = global_best_param_groups[0]['params']

        if self.checkIfParticleIsBest(testPos,testGlob) == True:
            # print(closure())
            # print("Will update this position now with SGD")
            ul = GDforPSO.SGDTimeOnParticlePos(self.listOfModelParameters)
            ul.changeWeights(self.position)
            newPos = ul.itsTimeIthink()


            for i in range(len(newPos)):
                for j in range(len(self.param_groups[i]['params'])):
                    self.param_groups[i]['params'][j].data = newPos[i]['params'][j].data
                    self.position[i]['params'][j].data = newPos[i]['params'][j].data
            # print(closure())

            # There is a fundamental flaw and that is that during the initizal stage, each iteration of the particle is likely to lead to a new global and so this gradient descent isn't called frequently, but rather only towards the end
        else:


        # if self.checkIfParticleIsBest(position_group_params, global_best_params) == False:
        #     print(position_group['params'])
        #     ul = GDforPSO.SGDTimeOnParticlePos(self.data)
        #     ul.changeWeights(position_group_params,counter)
        #     newPos = ul.itsTimeIthink()
        #
        #     new_position_params = newPos["params"]
        #     new_velocity_params = velocity_group_params
        #     print("Will update this position now with sgd")
        #     print(new_position_params)
        #     for p,m in zip(position_group_params, master_params):
        #         m.data = p.data
            # self.param_groups = newPos
            # Because our parameters are not a single tensor, we have to iterate over each group, and then each param in
            # each group.

            for position_group, velocity_group, personal_best, global_best, master in zip(self.position, self.velocity,
                                                                                          self.best_known_position,
                                                                                          global_best_param_groups,
                                                                                          self.param_groups):

                position_group_params = position_group['params']
                velocity_group_params = velocity_group['params']
                personal_best_params = personal_best['params']
                global_best_params = global_best['params']
                master_params = master['params']
                new_position_params = []
                new_velocity_params = []


                for p, v, pb, gb, m in zip(position_group_params, velocity_group_params, personal_best_params,
                                           global_best_params, master_params):

                    rand_personal = torch.rand_like(v)
                    rand_group = torch.rand_like(v)
                    new_velocity = (self.inertial_weight * v
                                    + self.cognitive_coefficient * rand_personal * (pb - p)
                                    + self.social_coefficient * rand_group * (gb - p)
                                    )
                    new_velocity_params.append(new_velocity)
                    new_position = p + new_velocity
                    new_position_params.append(new_position)
                    m.data = new_position.data  # Update the model, so we can use it for calculating loss
                position_group['params'] = new_position_params
                velocity_group['params'] = new_velocity_params

        # Really crummy way to update the parameter weights in the original model.
        # Simply changing self.param_groups doesn't update the model.
        # Nor does changing its elements or the raw values of 'param' of the elements.
        # We have to change the underlying tensor data to point to the new positions
            for i in range(len(self.position)):
                for j in range(len(self.param_groups[i]['params'])):
                    self.param_groups[i]['params'][j].data = self.param_groups[i]['params'][j].data

        # Calculate new loss after moving and update the best known position if we're in a better spot
        new_loss = closure()
        if new_loss < self.best_known_loss_value:
            self.best_known_position = clone_param_groups(self.position)
            self.best_known_loss_value = new_loss
        return new_loss

    def checkIfParticleIsBest(self,particlePos,globalPos):
        lengthTotal = len(particlePos)
        same = True
        for counter in range(lengthTotal):
            if torch.equal(particlePos[counter],globalPos[counter]) == False:
                same = False
                break
        return same

class GDPSO(GenericPSO):
    r"""
    Algorithm from Wikipedia: https://en.wikipedia.org/wiki/Particle_swarm_optimization
    Let S be the number of particles in the swarm, each having a position xi ∈ ℝn in the search-space
    and a velocity vi ∈ ℝn. Let pi be the best known position of particle i and let g be the best known
    position of the entire swarm.
    The values blo and bup represent the lower and upper boundaries of the search-space respectively.
    The w parameter is the inertia weight. The parameters φp and φg are often called cognitive coefficient and
    social coefficient.

    The termination criterion can be the number of iterations performed, or a solution where the adequate
    objective function value is found. The parameters w, φp, and φg are selected by the practitioner and control
    the behaviour and efficacy of the PSO method.

    for each particle i = 1, ..., S do
        Initialize the particle's position with a uniformly distributed random vector: xi ~ U(blo, bup)
        Initialize the particle's best known position to its initial position: pi ← xi
        if f(pi) < f(g) then
            update the swarm's best known position: g ← pi
        Initialize the particle's velocity: vi ~ U(-|bup-blo|, |bup-blo|)
    while a termination criterion is not met do:
        for each particle i = 1, ..., S do
            for each dimension d = 1, ..., n do
                Pick random numbers: rp, rg ~ U(0,1)
                Update the particle's velocity: vi,d ← w vi,d + φp rp (pi,d-xi,d) + φg rg (gd-xi,d)
            Update the particle's position: xi ← xi + vi
            if f(xi) < f(pi) then
                Update the particle's best known position: pi ← xi
                if f(pi) < f(g) then
                    Update the swarm's best known position: g ← pi


    :param params:iterable of parameters to optimize or dicts defining parameter groups
    :param inertial_weight: float representing inertial weight of the particles
    :param cognitive_coefficient: float representing cognitive coefficient of the particles
    :param social_coefficient: float representing social coefficient of the particles
    :param num_particles: int representing the number of particles in the swarm
    :param max_param_value: Maximum value of the parameters in the search space
    :param min_param_value: Minimum value of the parameters in the search space
    """

    def __init__(self,model,
                 params: Iterable[torch.nn.Parameter],
                 inertial_weight: float = .9,
                 cognitive_coefficient: float = 1.,
                 social_coefficient: float = 1.,
                 num_particles: int = 100,
                 max_param_value: float = 10.,
                 min_param_value: float = -10.):
        self.num_particles = num_particles
        self.inertial_weight = inertial_weight
        self.cognitive_coefficient = cognitive_coefficient
        self.social_coefficient = social_coefficient
        self.max_param_value = max_param_value
        self.min_param_value = min_param_value
        self.model = model
        kwargs = {'inertial_weight': inertial_weight,
                  'cognitive_coefficient': cognitive_coefficient,
                  'social_coefficient': social_coefficient,
                  'model': model,
                  'max_param_value': max_param_value,
                  'min_param_value': min_param_value
                  }
        super().__init__(params, num_particles, Particle, particle_kwargs=kwargs)