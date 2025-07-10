import numpy as np
import csv
import loss_function
from scipy import optimize as scipy_optimize
import model as mod
import log


def check_content(content, word, default):  # Returns string/float/int/bool/None
    if word in content.keys():
        return content[word]
    else:
        return default


class Algorithm:
    def __init__(self, content):
        self.content = content
        self.result = None
        self.max_iter = check_content(content, "max_iter", 1000)
        self.x0 = np.ndarray([])
        self.bounds = None
        self.setup_x0()
        self.setup_bounds()

    def setup_x0(self) -> None:
        if "x0" not in self.content.keys():
            raise KeyError("Could not find 'x0' in config")
        if "num_of_params" not in self.content.keys():
            raise KeyError("Could not find 'num_of_params' in config")
        num_of_params = self.content["num_of_params"]
        with open(self.content["x0"]) as csvfile:  # for param limits
            reader = csv.reader(csvfile)
            x0 = []
            for val in next(reader):
                x0.append(float(val))

        if num_of_params != len(x0):
            raise ValueError("Number of parameters in 'x0' does not match number of parameters in 'num_of_params'")

        self.x0 = np.array(x0)

    def setup_bounds(self) -> None:
        bounds_file = check_content(self.content, "bounds_file", None)
        if bounds_file is None:
            return

        with open(bounds_file) as csvfile:  # for param limits
            reader = csv.reader(csvfile)
            param_names = []
            for name in next(reader):
                param_names.append(name)

            min_values = []
            for min_value in next(reader):
                min_value = min_value.strip()
                min_values.append(float(min_value))

            max_values = []
            for max_value in next(reader):
                max_value = max_value.strip()
                max_values.append(float(max_value))
            bounds = []
            for min_value, max_value in zip(min_values, max_values):
                bounds.append((min_value, max_value))
            self.bounds = bounds


class NelderMead(Algorithm):
    def __init__(self, content):
        super().__init__(content)
        self.xatol = check_content(content, "xatol", 1e-4)
        self.fatol = check_content(content, "fatol", 1e-4)
        self.maxfev = check_content(content, "maxfev", None)
        self.options = {}

    def make_options(self):
        self.options = {"xatol": self.xatol, # Parameter tolerance
                        "fatol": self.fatol, # Loss function tolerance
                        "maxfev": self.maxfev, #Maximium loss function evaluations
                        "adaptive": True, # Using adaptive Nelder-Mead (it works better for larger dimension problems)
                        "maxiter": self.max_iter} #Maxiumium number of iterations for algorithm

    def run(self, loss_func, seed) -> scipy_optimize.OptimizeResult:
        del seed
        self.make_options()
        result = scipy_optimize.minimize(loss_func.run_loss,
                                         x0=self.x0,
                                         method='Nelder-Mead',
                                         options=self.options,
                                         bounds=self.bounds)

        return result


class StornPrice(Algorithm):
    def __init__(self, content):
        super().__init__(content)
        self.strategy = check_content(content, "strategy", "best1bin")
        self.pop_size = check_content(content, "pop_size", 15)
        self.polish = check_content(content, "polish", True)
        self.recombination = check_content(content, "recombination", 0.7)
        self.workers = check_content(content, "workers", -1)  # TODO not a part configuration
        self.tol = check_content(content, "tol", 0.01)

    def check_bounds(self):
        if self.bounds is None:
            raise KeyError("In StornPrice bounds for parameters must be defined")

    def run(self, loss_func, seed) -> scipy_optimize.OptimizeResult:
        self.check_bounds()
        result = scipy_optimize.differential_evolution(
            loss_func.run_loss,
            x0=self.x0,
            bounds=self.bounds,
            maxiter=self.max_iter, # Max num of loss function evals = pop_size*num_of_params*max_iter (before polish)
            strategy=self.strategy, # Differential evolution strategy to use
            disp=log.VERBOSE, # Prints best function value after each iteration
            workers=self.workers, # Number of parallel processes
            popsize=self.pop_size, # Population size for each generation
            polish=self.polish, # Do you call minimize function L-BFGS-B after the DE or not
            recombination=self.recombination, # Probablity for more exploration of parameters
            tol=self.tol, # Relative tolerance for convergence
            seed=seed) # Seed for random number generator
        return result


ALGORITHMS = {
    "NelderMead": NelderMead,
    "StornPrice": StornPrice,
}


class Optimize:
    def __init__(self, content, models: mod.Models, seed: int):
        self.content = content[0]
        self.x0 = None
        self.bounds = None
        self.algorithm = check_content(self.content, "algorithm", None)
        self.loss_type = check_content(self.content, "loss_type", None)
        self.models = models
        self.seed = seed

        self.run_optimize()

    def setup_loss_type(self):
        if self.loss_type in loss_function.LOSSFUNCTIONS:
            log.print_verbose(f"Using loss type: {self.loss_type}")
            loss_func = loss_function.LOSSFUNCTIONS[self.loss_type](self.content, self.models.model(self.content["model"]))
        else:
            raise NotImplementedError(f"Loss function '{self.loss_type}' is not implemented. "
                                      f"Available loss functions: {list(loss_function.LOSSFUNCTIONS.keys())}")
        return loss_func

    def setup_algorithm(self):

        if self.algorithm in ALGORITHMS:
            log.print_verbose(f"Using algorithm: {self.algorithm}")
            return ALGORITHMS[self.algorithm](self.content)
        else:
            raise NotImplementedError(f"Algorithm '{self.algorithm}' is not implemented. Available algorithms: {list(ALGORITHMS.keys())}")


    def save_result(self, result) -> None:
        file_name = self.content["result_file"]
        log.print_verbose(f"Saving result to : {file_name}")
        with open(file_name, "w") as file:
            file.write(str(result))
            file.write(f"X: {result.x}, fun: {result.fun}")

    def run_optimize(self):
        loss_func = self.setup_loss_type()
        loss_func.setup()

        algo = self.setup_algorithm()

        result = algo.run(loss_func=loss_func, seed=self.seed)
        self.save_result(result)
