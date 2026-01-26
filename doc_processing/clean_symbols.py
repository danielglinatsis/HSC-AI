# TODO: Implement "mapping" of math characters to text

import re

integral_mapping = {
    'dx' : 'dx (integration)',
    'dt' : 'dt (integration)'
    }

def clean_math(data):
    """
    Cleans all math symbols to improve readability
    Expects a dictionary with 'metadata' and 'questions'
    """
    if not isinstance(data, dict):
        all_qs = data
        metadata = []
    else:
        all_qs = data.get('questions', [])
        metadata = data.get('metadata', [])

    cleaned_questions = []

    for exam_qs in all_qs:
        cleaned_exam_qs = []
        for q in exam_qs:
            text = q.get('text', '')
            for key, replacement in integral_mapping.items():
                text = re.sub(rf'(?<![a-zA-Z]){key}(?![a-zA-Z])', replacement, text)
            cleaned_exam_qs.append({
                **q,
                'text': text
            })
        cleaned_questions.append(cleaned_exam_qs)

    result = {
        "metadata": metadata,
        "questions": cleaned_questions
    }
    return result

"""
PAPER - 2024
Question 5:
What is  ]6 x+ 1g3dx ?
24]6 x+ 1g4+C
4]6 x+ 1g4+C
3]6 x+ 1g4+C
2]6 x+ 1g4+C'

Question 27
(a)
Find the derivative of x 2 tan x.
(b)
Hence, find  ^x tan x+ 1h2dx .
"""

"""
Paper - 2023

Question 5
The diagram shows the graph y =ƒ( x ), where ƒ( x ) is an odd function.
The shaded area is 1 square unit.
The number a, where a > 1, is chosen so that
ƒ( x ) dx = 0 .
NOT TO
SCALE
What is the value of
ƒ( x ) dx ?

Question 17
Find
xx2 + 1 dx .
"""

"""
Paper - 2022
Question 6
What is
dx ?
(2x + 1)2
2x +1
2 ( 2x +1 )
2 ln ( 2x +1 ) +C
ln ( 2x +1 ) +C

Question 8
The graph of the even function y =â( x ) is shown.
The area of the shaded region A is
and the area of the shaded region B is .
NOT TO
SCALE
y =â( x )
What is the value of
â( x ) dx ?

Question 13
Use two applications of the trapezoidal rule to find an approximate
value of
1 +x2 dx . Give your answer correct to 2 decimal places.

Question 18
(a)
Differentiate y =(x2 + 1)  .
(b)
Hence, or otherwise, find x x2 + 1)dx .

Question 29
(a)
The diagram shows the graph of y = 2x. Also shown on the diagram are the
first 5 of an infinite number of rectangular strips of width 1 unit and height
y = 2−x for non-negative integer values of x. For example, the second rectangle
shown has width 1 and height
Graph
The sum of the areas of the rectangles forms a geometric se
Show that the limiting sum of this series is 2.
ries.
(b)
Show that
2−x dx =
16 ln 2
"""

"""
Paper - 2021
Question 15
Evaluate ⎮2x + 4 dx.⌡–2

Question 27
Kenzo has a solar powered phone charger. Its power, P, can be modelled by the       
function
P(t)= 400 sin
t  , 0 ≤t≤ 12 , where t is the number of hours after sunrise.
(a)
Sketch the graph of P for 0 ≤t≤ 12 .
Power is the rate of change of energy. Hence the amount of energy, E units, generated
by the solar powered phone charger from t=a to t=b, where 0 ≤a≤b≤ 12 is
given by
E = ⎮P t( )dt .a p
(b) Show that E= cos− cos

Question 28 (continued)
(b) A new function g(x) is found by taking the graph of y=−â(−x) and translating        
it by 5 units to the right.
Sketch the graph of y=g(x) showing the x-intercept and the asymptote.
(c) Hence, find the exact value of ⎮g x ( )dx .
"""


"""
Paper - 2020
Question 4
What is e + e3x dx ?
ex+ 3e3x+c
ex+e3x+c
e+ 3e3x+c
e+e3x+c

Question 7
What is the value of ⎮ƒ ( )x dx ?
24 + 2p
24 + 4p
30 + 2p
30 + 4p

Question 13
Evaluate sec2 x dx .

Question 17
Find ⎮dx . 4 + x2

Question 18
(a) Differentiate e2x(2x +1) .
(b) Hence, find x +1 e2x dx .

Question 20
Kenzo is driving his car along a road while his friend records the velocity of    
the car, v(t), in km/h every minute over a 5-minute period. The table gives the   
velocity v(t) at time t hours.
v(t)
The distance covered by the car over the 5-minute period is given by
⌠60 v t( )dt.
Use the trapezoidal rule and the velocity at each of the six time values to find the
approximate distance in kilometres the car has travelled in the 5-minute period. Give
your answer correct to one decimal place.
"""