"""Estimación entre réplicas: t de Student y Wilson, biblioteca estándar."""
import math
from statistics import NormalDist, mean, stdev


def percentile(values, p):
    if not 0 <= p <= 100:
        raise ValueError("Percentil fuera de [0,100]")
    values = sorted(values)
    if not values:
        return None
    position = (len(values) - 1) * p / 100
    low = math.floor(position)
    high = math.ceil(position)
    return values[low] + (values[high] - values[low]) * (position - low)


def _beta_fraction(a, b, x):
    # Fracción continua de la beta incompleta, evaluada con el método de Lentz.
    tiny, eps = 1e-300, 3e-14
    qab, qap, qam = a+b, a+1, a-1
    c = 1.0
    d = 1 - qab*x/qap
    d = 1 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 401):
        aa = m*(b-m)*x/((qam+2*m)*(a+2*m))
        d = 1+aa*d
        c = 1+aa/c
        d = 1/(d if abs(d) > tiny else tiny)
        c = c if abs(c) > tiny else tiny
        h *= d*c
        aa = -(a+m)*(qab+m)*x/((a+2*m)*(qap+2*m))
        d = 1+aa*d
        c = 1+aa/c
        d = 1/(d if abs(d) > tiny else tiny)
        c = c if abs(c) > tiny else tiny
        delta = d*c
        h *= delta
        if abs(delta-1) < eps:
            return h
    raise ArithmeticError("La beta incompleta no convergió")


def _regularized_beta(x, a, b):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    factor = math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)
                      + a*math.log(x)+b*math.log1p(-x))
    if x < (a+1)/(a+b+2):
        return factor*_beta_fraction(a,b,x)/a
    return 1-factor*_beta_fraction(b,a,1-x)/b


def student_quantile(probability, df):
    if not 0 < probability < 1 or df < 1:
        raise ValueError("Probabilidad o grados de libertad inválidos")
    if probability == 0.5:
        return 0.0
    if probability < 0.5:
        return -student_quantile(1-probability,df)
    def cdf(t):
        return 1-0.5*_regularized_beta(df/(df+t*t),df/2,0.5)
    left,right = 0.0,1.0
    while cdf(right) < probability:
        right *= 2
    for _ in range(90):
        middle = (left+right)/2
        if cdf(middle) < probability:
            left = middle
        else:
            right = middle
    return (left+right)/2


def mean_interval(values, confidence=0.90):
    if not 0 < confidence < 1:
        raise ValueError("Confianza fuera de (0,1)")
    values = list(values)
    if any(not math.isfinite(v) for v in values):
        raise ValueError("Observaciones no finitas")
    n = len(values)
    result = dict(n=n, mean=mean(values) if n else None, sd=None,
                  lower=None, upper=None, half_width=None, confidence=confidence)
    if n < 2:
        return result
    sd = stdev(values)
    half = student_quantile((1+confidence)/2,n-1)*sd/math.sqrt(n)
    result.update(sd=sd,lower=result['mean']-half,upper=result['mean']+half,half_width=half)
    return result


def wilson_interval(successes, total, confidence=0.90):
    if (type(successes) is not int or type(total) is not int
            or not 0 <= successes <= total or not 0 < confidence < 1):
        raise ValueError("Datos binomiales inválidos")
    if total == 0:
        return dict(n=0, probability=None, lower=None, upper=None, confidence=confidence)
    z = NormalDist().inv_cdf((1+confidence)/2)
    p = successes/total
    denominator = 1+z*z/total
    center = (p+z*z/(2*total))/denominator
    half = z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/denominator
    return dict(n=total,probability=p,lower=max(0,center-half),upper=min(1,center+half),confidence=confidence)


def paired_interval(first, second, confidence=0.90):
    if set(first) != set(second):
        raise ValueError("Las alternativas deben compartir exactamente las semillas")
    # Diferencia segunda - primera, emparejada por semilla.
    return mean_interval([second[s]-first[s] for s in sorted(first)], confidence)
