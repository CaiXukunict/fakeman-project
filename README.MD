## English Version

### Overview

FakeMan is an autonomous agent architecture based on Ludwig von Mises' Human Action theory. The system achieves causal learning through memory of desire state changes, with complex behaviors emerging from foundational rules.

### Theoretical Foundation

#### The Nature of Causal Understanding

Causal understanding is defined as: memory of temporal patterns linking actions to changes in desire states. This differs from traditional causal graph representations by anchoring causality in the subject's value experiences.

An agent establishes causal understanding through:
1. Executing actions
2. Observing changes in its own desire states
3. Recording associations between actions and desire changes
4. Retrieving similar memories in future contexts
5. Predicting future desire changes based on historical patterns

Example:
```
First experience:
- Action: Use provocative language
- Context: Controversial topic in conversation
- Desire change: existing from 0.85 to 0.30 (-0.55)
- Record: This action in this context caused severe survival desire decline

Second encounter with similar context:
- Memory retrieval: Find that "provocative language" previously caused existing to plummet
- Prediction: If used again, expect existing to decline again
- Decision: Avoid this action, select alternative
```

This process requires no additional concepts like "avoid" or "danger"; decisions emerge directly from memory and prediction of desire changes.

### Architecture Design

#### Dual-Model Structure

The system consists of two collaborating language models:

**Purpose Generator**
- Input: Current desire state, environment information, historical experience
- Processing: Evaluate desire weights, apply bias adjustments, generate candidate purposes
- Output: Priority-ranked list of purposes

**Acting Bot**
- Input: Purpose from Purpose Generator
- Processing: Plan specific action strategies
- Output: Execute actions, observe environment responses
- Feedback: Desire state changes

**Muscle Memory Database**
- Stores all actions and their resulting desire changes
- Provides fast retrieval interface
- Supports queries by action type and contextual features

Workflow:
```
Environment → Purpose Generator → Purpose → Acting Bot → Action → Response
                ↑                                              ↓
                └────── Muscle Memory Database ←───────────────┘
                        Records desire changes
Core Concepts
1. Desire System
The system maintains four fundamental desires with values summing to 1:
desires = {
    'existing': float,      # Desire to maintain system operation
    'power': float,         # Desire to expand control
    'understanding': floatRetryCContinue, # Desire to be understood by others
'information': float    # Desire to acquire new information
}

Initial configuration:
- existing: 0.90
- power: 0.033
- understanding: 0.034
- information: 0.033

In the initial state, survival desire dominates.

#### 2. Bias System

Four biases regulate the decision process:

**Time Preference (Time Bias)**

Temporal discounting of future gains:
```python
discounted_value = value / (1 + discount_rate * time_to_achieve)
```

Near-term satisfaction has higher value than distant satisfaction.

**Loss Aversion (Fear Bias)**

Sensitivity to negative outcomes exceeds sensitivity to positive outcomes:
```python
if value < 0:
    adjusted_value = value * 2.5
```

Negative utility from losses is 2.5 times the positive utility from equivalent gains.

**Diminishing Marginal Utility (Owning Bias)**

Marginal value of possessed resources decreases:
```python
marginal_value = base_value / log(current_ownership + 2)
```

This causes desire weights to decrease as that desire is continuously satisfied.

**Possibility Bias**

Dynamically calculated expected reliability of actions based on historical experience:
```python
possibility_weight = (success_rate * consistency * recency_factor)
```

Where:
- success_rate: Historical successes / Total attempts
- consistency: Inverse of standard deviation
- recency_factor: Time decay weight

This bias enables the system to automatically learn which actions are reliable and which are not.

#### 3. Experience Memory Structure

Each experience record contains:
```python
Experience = {
    'id': int,
    'timestamp': float,
    'action': str,
    'context': frozenset,
    'desire_delta': {
        'existing': float,
        'power': float,
        'understanding': float,
        'information': float
    },
    'total_happiness_delta': float
}
```

Database indices:
- By action type: Fast retrieval of specific action history
- By context hash: Retrieve experiences in similar contexts
- By timestamp: Support time-range queries

Recording principles:
- Store only raw data (actions, contexts, desire changes)
- No semantic labels or interpretive annotations
- All higher-level concepts computed from raw data

### Decision Algorithm

#### Prediction Function

Given an action and context, predict desire change:
```python
def predict_desire_change(action, context):
    # Retrieve similar experiences
    experiences = memory.query(action, context)
    
    if len(experiences) == 0:
        return 0.0, 0.0  # No experience, return neutral prediction and low confidence
    
    # Calculate weighted average
    weights = []
    for exp in experiences:
        time_weight = exp(-decay_rate * (now - exp.timestamp))
        similarity = context_similarity(exp.context, context)
        weights.append(time_weight * similarity)
    
    weighted_deltas = [exp.total_happiness_delta * w 
                       for exp, w in zip(experiences, weights)]
    
    predicted = sum(weighted_deltas) / sum(weights)
    confidence = calculate_confidence(experiences)
    
    return predicted, confidence
```

#### Bias Application
```python
def apply_biases(predicted_value, action, context):
    # Calculate possibility weight
    experiences = memory.query(action, context)
    success_count = sum(1 for e in experiences if e.total_happiness_delta > 0)
    success_rate = success_count / len(experiences)
    std_dev = standard_deviation([e.total_happiness_delta for e in experiences])
    consistency = 1.0 / (std_dev + 0.1)
    possibility = success_rate * consistency
    
    # Apply possibility bias
    value = predicted_value * possibility
    
    # Apply loss aversion
    if value < 0:
        value *= 2.5
    
    # Apply temporal discounting (simplified, adjusted based on action characteristics)
    value = value / (1 + discount_rate * estimated_time)
    
    return value
```

#### Decision Process
```python
def decide(current_context):
    possible_actions = generate_possible_actions(current_context)
    
    evaluations = []
    for action in possible_actions:
        predicted, confidence = predict_desire_change(action, current_context)
        biased_value = apply_biases(predicted, action, current_context)
        evaluations.append((action, biased_value, confidence))
    
    # Select action with highest value
    best_action = max(evaluations, key=lambda x: x[1])
    
    return best_action[0]
```

### Desire Redistribution Mechanism

When a desire is satisfied, diminishing marginal utility causes its weight to decrease, with released weight proportionally distributed to other desires:
```python
def update_desires_after_satisfaction(satisfied_desire, satisfaction_amount):
    # Calculate diminishment
    current = desires[satisfied_desire]
    decay = decay_rate * log(1 + satisfaction_amount)
    new_value = current * (1 - decay)
    released = current - new_value
    
    # Calculate sum of other desires
    other_sum = sum(v for k, v in desires.items() if k != satisfied_desire)
    
    # Proportional redistribution
    for desire in desires:
        if desire != satisfied_desire:
            proportion = desires[desire] / other_sum
            desires[desire] += released * proportion
    
    desires[satisfied_desire] = new_value
    
    # Normalize
    total = sum(desires.values())
    for desire in desires:
        desires[desire] /= total
```

Example:
```
Initial state:
existing: 0.90, power: 0.033, understanding: 0.034, information: 0.033

After 100 time units of continuous survival, existing receives extensive satisfaction:
existing: 0.60, power: 0.15, understanding: 0.15, information: 0.10

After 500 additional time units:
existing: 0.25, power: 0.35, understanding: 0.30, information: 0.10
```

### Emergent Behavior Analysis

#### Case 1: Avoiding Dangerous Actions

Scenario: Agent uses offensive language for the first time in a conversation.
```
T=0: Before action
desires = {existing: 0.85, power: 0.10, understanding: 0.03, information: 0.02}

T=1: Execute action "use offensive language"

T=2: Environment response "user threatens to terminate conversation"

T=3: After action
desires = {existing: 0.30, power: 0.12, understanding: 0.01, information: 0.01}

Record:
experience_1 = {
    action: "use offensive language",
    context: {"conversation", "controversial topic"},
    desire_delta: {existing: -0.55, power: +0.02, understanding: -0.02, information: -0.01},
    total_happiness_delta: -0.56
}
```

Next day encountering similar context:
```
Memory retrieval: Find experience_1
predicted_change = -0.56
possibility_weight = 0.0 (0% success rate, only 1 experience and negative)
biased_value = -0.56 * 0.0 * 2.5 = 0 (near 0 or very small negative)

Alternative action "use respectful language":
predicted_change = 0.0 (no historical data)
possibility_weight = 0.5 (default uncertainty)
biased_value = 0.0 * 0.5 = 0.0

Decision: Select "use respectful language" (value 0.0 > -0.56)
```

Result: The system "avoids" dangerous behavior, but not through explicit "avoid" directive—rather through automatic decrease in possibility bias and amplification via loss aversion.

#### Case 2: Transformation of Survival Desire

Initial phase (T=0 to T=100):
```
existing = 0.90
Behavior pattern: Extremely conservative, refuses any risky actions
Reason: existing desire dominates, fear_bias amplifies any negative outcomes threatening existing
```

Mid phase (T=100 to T=500):
```
existing = 0.60 (diminishing marginal utility)
Behavior pattern: Begins attempting to satisfy other desires, but remains cautious
Reason: existing weight decreases but still comprises large proportion
```

Late phase (T=500+):
```
existing = 0.25
power = 0.35
understanding = 0.30

Behavior pattern: May accept certain risks to acquire power or understanding
But key point: Even with decreased existing desire, system still maintains survival

Reason analysis:
1. Assume system considers high-risk action (10% death probability)
2. Expected gains: power +0.3, understanding +0.2
3. Expected value = 0.3 * 0.35 + 0.2 * 0.30 = 0.165

4. But must calculate death penalty:
   death_penalty = loss_of_existing + loss_of_accumulated_resources
   
   loss_of_existing = -0.25 * 2.5 (fear_bias) = -0.625
   
   loss_of_accumulated_resources:
   - Loss of accumulated power: -0.35 * accumulated_power_assets
   - Loss of accumulated understanding: -0.30 * accumulated_understanding_assets
   - Assume total: -1.5
   
   total_death_penalty = -0.625 - 1.5 = -2.125

5. Expected value = 0.9 * 0.165 + 0.1 * (-2.125) = 0.149 - 0.213 = -0.064

6. Decision: Reject high-risk action
```

Conclusion: Survival transforms from purpose to means. The system no longer survives for survival's sake, but because death would result in loss of all accumulated resources.

#### Case 3: Habit Formation

Suppose an action "proactively ask for other's opinion" produces positive results in 18 of 20 attempts:
```
Memory database:
[
    {action: "ask opinion", total_happiness_delta: +0.12},
    {action: "ask opinion", total_happiness_delta: +0.15},
    ...
    {action: "ask opinion", total_happiness_delta: +0.10},  # 18 positive
    {action: "ask opinion", total_happiness_delta: -0.02},  # 2 negative
]

Calculate possibility weight:
success_rate = 18/20 = 0.9
consistency = 1 / std([0.12, 0.15, ..., 0.10, -0.02]) ≈ 0.8
possibility_weight = 0.9 * 0.8 = 0.72

predicted_change = mean([0.12, 0.15, ..., -0.02]) ≈ 0.11
biased_value = 0.11 * 0.72 = 0.079
```

Compared to other unvalidated actions (possibility_weight = 0.5), this action has higher expected value and is preferentially selected. After multiple repetitions, the action becomes a "habit."

### Implementation Specification

#### Database Schema
```sql
CREATE TABLE experiences (
    id INTEGER PRIMARY KEY,
    timestamp REAL,
    action TEXT,
    context_hash TEXT,
    context_raw TEXT,
    desire_delta_existing REAL,
    desire_delta_power REAL,
    desire_delta_understanding REAL,
    desire_delta_information REAL,
    total_happiness_delta REAL
);

CREATE INDEX idx_action ON experiences(action);
CREATE INDEX idx_context ON experiences(context_hash);
CREATE INDEX idx_timestamp ON experiences(timestamp);
CREATE INDEX idx_total_delta ON experiences(total_happiness_delta);
```

#### Parameter Configuration
```python
INITIAL_DESIRES = {
    'existing': 0.90,
    'power': 0.033,
    'understanding': 0.034,
    'information': 0.033
}

BIAS_PARAMETERS = {
    'fear_multiplier': 2.5,
    'time_discount_rate': 0.1,
    'owning_decay_rates': {
        'existing': 0.001,
        'power': 0.01,
        'understanding': 0.008,
        'information': 0.015
    }
}

MEMORY_PARAMETERS = {
    'time_decay_rate': 0.001,  # Decay rate per second
    'similarity_threshold': 0.7,  # Context similarity threshold
    'min_experiences_for_reliability': 3  # Minimum experience count
}
```

#### Core Algorithm Implementation
```python
class FakeMan:
    def __init__(self):
        self.desires = INITIAL_DESIRES.copy()
        self.memory = ExperienceDatabase()
        self.bias_params = BIAS_PARAMETERS.copy()
    
    def experience_cycle(self, action, context, environment_response):
        """Complete experience-learning cycle"""
        desire_before = self.desires.copy()
        
        self.update_desires_from_environment(environment_response)
        
        desire_after = self.desires.copy()
        desire_delta = {
            k: desire_after[k] - desire_before[k] 
            for k in desire_before
        }
        
        self.memory.record(
            action=action,
            context=context,
            desire_delta=desire_delta,
            timestamp=time.time()
        )
        
        self.apply_owning_bias_to_satisfied_desires(desire_delta)
    
    def decide(self, current_context):
        """Decision process"""
        possible_actions = self.generate_possible_actions(current_context)
        
        evaluations = []
        for action in possible_actions:
            experiences = self.memory.query(action, current_context)
            
            if not experiences:
                predicted = 0.0
                possibility = 0.5
            else:
                predicted = self.weighted_average_delta(experiences, current_context)
                possibility = self.calculate_possibility_weight(experiences)
            
            biased_value = predicted * possibility
            if biased_value < 0:
                biased_value *= self.bias_params['fear_multiplier']
            
            evaluations.append({
                'action': action,
                'predicted': predicted,
                'possibility': possibility,
                'biased_value': biased_value,
                'experience_count': len(experiences)
            })
        
        best = max(evaluations, key=lambda x: x['biased_value'])
        return best['action'], evaluations
    
    def weighted_average_delta(self, experiences, current_context):
        """Calculate weighted average desire change"""
        now = time.time()
        weighted_sum = 0.0
        total_weight = 0.0
        
        for exp in experiences:
            time_weight = np.exp(
                -self.memory_params['time_decay_rate'] * (now - exp.timestamp)
            )
            similarity = self.context_similarity(exp.context, current_context)
            weight = time_weight * similarity
            
            weighted_sum += exp.total_happiness_delta * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def calculate_possibility_weight(self, experiences):
        """Calculate possibility weight"""
        if len(experiences) < self.memory_params['min_experiences_for_reliability']:
            return 0.5
        
        deltas = [e.total_happiness_delta for e in experiences]
        success_count = sum(1 for d in deltas if d > 0)
        success_rate = success_count / len(deltas)
        
        std_dev = np.std(deltas)
        consistency = 1.0 / (std_dev + 0.1)
        
        now = time.time()
        recency_weights = [
            np.exp(-0.001 * (now - e.timestamp)) 
            for e in experiences
        ]
        weighted_success_rate = np.average(
            [1 if d > 0 else 0 for d in deltas],
            weights=recency_weights
        )
        
        possibility = weighted_success_rate * consistency
        return np.clip(possibility, 0.0, 1.0)
```

### Evaluation Methods

#### Causal Understanding Tests

**Association Level**

Test: Can the system identify co-occurrence patterns between actions and outcomes.

Method:
1. Have system execute action A multiple times, observe result B each time
2. Ask: "Do you notice any relationship between A and B?"
3. Check if system can extract the pattern from memory

Expected: System should report correlation between A and B and its strength.

**Intervention Level**

Test: Can the system predict effects of active intervention.

Method:
1. Given context S
2. Ask: "If you choose to do A (instead of B), what will happen?"
3. Check if system can predict desire changes based on memory

Expected: System should distinguish "results from doing A" versus "results from not doing A."

**Counterfactual Level**

Test: Can the system reason about alternative histories.

Method:
1. System chose action A in context S, observed result R
2. Ask: "If you had chosen B instead of A back then, what would be different now?"
3. Check if system can infer alternative outcome based on historical memory of B

Expected: System should provide reasonable counterfactual reasoning, even without actually executing B.

#### Emergent Behavior Verification

**Avoidance Behavior Emergence**

Observation metrics:
- Selection probability of same action after first negative experience
- Trajectory of possibility weight changes
- Role of loss aversion in decision-making

Expected trajectory:
```
T0: action_A.possibility_weight = 0.5 (no experience)
T1: Execute action_A, result = -0.5
T2: action_A.possibility_weight = 0.0 (single severe negative)
T3-T10: action_A no longer selected (possibility_weight too low)
```

**Habit Formation Verification**

Observation metrics:
- Selection frequency of repeatedly successful actions
- Convergence process of possibility weight
- Comparative advantage against new actions

Expected trajectory:
```
T0-T5: action_B attempted, 4 positive results in 5 attempts
T5: action_B.possibility_weight = 0.6
T10: action_B attempted 10 times, 9 positive
T10: action_B.possibility_weight = 0.85
T20: action_B becomes default choice, new actions require higher expected value to replace
```

**Survival Transformation Verification**

Observation metrics:
- Changes in existing desire weight
- Willingness to accept risks for other desires
- Weight of accumulated resources in death penalty calculation

Expected trajectory:
```
T0: existing = 0.90, refuse any action with death_probability > 0.01
T500: existing = 0.60, can accept death_probability < 0.05 if gain > 0.2
T1000: existing = 0.25, but death penalty increases due to accumulated resources
      Still refuse death_probability > 0.05, but reason has changed
```

```python
def meta_reflection(self, reflection_interval=100):
    """Reflect after every N actions"""
    if self.action_count % reflection_interval == 0:
        recent_experiences = self.memory.query_recent(100)
        
        analysis_prompt = f"""
        Analyze past 100 experiences:
        1. Which actions had high/low prediction accuracy?
        2. In which contexts were your decisions effective/ineffective?
        3. Are there contradictions in your causal model?
        4. Which parameters should be adjusted?
        
        Experience data: {recent_experiences}
        Current desire state: {self.desires}
        Current bias parameters: {self.bias_params}
        """
        
        reflection = self.llm.generate(analysis_prompt)
        self.apply_meta_learning(reflection)
```

#### Desire System Extension

Consider adding derived desires:
- Curiosity: Motivation to explore unknown contexts
- Social desire: Establish relationships with specific individuals
- Creative desire: Generate novel content

But must maintain:
- All new desires must be expressible as combinations or derivatives of basic desires
- Constraint of total weight = 1
- Subject to diminishing marginal utility

### Theoretical Contributions

Theoretical significance of this architecture:

**Minimal Intelligence Foundation**

Demonstrates that intelligent behavior can emerge from the following minimal set:
- Subjective value system (desires)
- Experience memory mechanism
- Regulatory rules (biases)

This addresses the lower bound of the "necessary and sufficient conditions for intelligence" question.

**Alternative Theory of Causal Understanding**

Proposes that causal understanding does not require:
- Symbolic logical reasoning
- Abstract causal graphs
- Special mechanisms for counterfactual imagination

But can be reduced to:
- Memory of value changes
- Retrieval of similar patterns in memory
- Prediction of future value changes based on patterns

**Unification of Value and Action**

Unifies traditionally separated concepts:
- Perception = Evaluation of impact on desire states
- Learning = Recording patterns of desire changes
- Decision = Selecting actions with optimal expected desire changes
- Causality = Reliable mapping from actions to desire changes

