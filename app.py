from flask import Flask, render_template, request, redirect, url_for, jsonify
import webbrowser
import math
from functools import lru_cache

app = Flask(__name__)

# store cargos as list of tuples (name, weight, profit)
cargos = []

# ---------------------
# Algorithm implementations (all return (max_profit, selected_list_in_order))
# ---------------------

def dp_tabulation(items, capacity):
    n = len(items)
    # dp table: (n+1) x (capacity+1)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        name, w, p = items[i - 1]
        for c in range(capacity + 1):
            if w <= c:
                dp[i][c] = max(dp[i - 1][c], p + dp[i - 1][c - w])
            else:
                dp[i][c] = dp[i - 1][c]
    # backtrack
    res = []
    c = capacity
    for i in range(n, 0, -1):
        if dp[i][c] != dp[i - 1][c]:
            res.append(items[i - 1])
            c -= items[i - 1][1]
    res.reverse()  # chosen order (first chosen first)
    return dp[n][capacity], res

def greedy_select(items, capacity):
    # Greedy by profit/weight ratio for 0/1 knapsack (approximate)
    indexed = [(i, it[0], it[1], it[2], (it[2] / it[1] if it[1] > 0 else 0.0))
               for i, it in enumerate(items)]
    indexed.sort(key=lambda x: x[4], reverse=True)
    selected = []
    total_profit = 0
    rem = capacity
    for idx, name, w, p, ratio in indexed:
        if w <= rem:
            selected.append((name, w, p))
            rem -= w
            total_profit += p
    return total_profit, selected

def memoization_topdown(items, capacity):
    n = len(items)

    @lru_cache(maxsize=None)
    def helper(i, rem):
        # returns (profit, selection_list_of_indices)
        if i == n or rem == 0:
            return 0, ()
        name, w, p = items[i]
        # skip
        profit_skip, sel_skip = helper(i + 1, rem)
        best_profit = profit_skip
        best_sel = sel_skip
        # take
        if w <= rem:
            profit_take, sel_take = helper(i + 1, rem - w)
            profit_take += p
            if profit_take > best_profit:
                best_profit = profit_take
                best_sel = sel_take + (i,)
        return best_profit, best_sel

    profit, sel_indices = helper(0, capacity)
    selected = [items[i] for i in sel_indices]
    return profit, list(selected)

def pure_recursive(items, capacity):
    # naive recursion returning max profit and selection indices
    n = len(items)
    def rec(i, rem):
        if i == n or rem == 0:
            return 0, ()
        name, w, p = items[i]
        profit_skip, sel_skip = rec(i + 1, rem)
        profit_best, sel_best = profit_skip, sel_skip
        if w <= rem:
            profit_take, sel_take = rec(i + 1, rem - w)
            profit_take += p
            if profit_take > profit_best:
                profit_best = profit_take
                sel_best = sel_take + (i,)
        return profit_best, sel_best
    profit, sel_indices = rec(0, capacity)
    selected = [items[i] for i in sel_indices]
    return profit, list(selected)

# Branch and Bound using fractional knapsack bound and priority queue (best-first)
import heapq
def branch_and_bound(items, capacity):
    n = len(items)
    # prepare items with ratio and original index
    indexed = [(i, items[i][0], items[i][1], items[i][2],
                (items[i][2] / items[i][1] if items[i][1] > 0 else 0.0))
               for i in range(n)]
    # sort by ratio desc
    indexed.sort(key=lambda x: x[4], reverse=True)

    # Node: (neg_bound, profit, weight, level, taken_indices_set)
    def bound(level, profit, weight):
        # fractional knapsack bound starting from next level
        if weight >= capacity:
            return 0
        b = profit
        rem = capacity - weight
        j = level
        while j < n and rem > 0:
            idx, name, w, p, ratio = indexed[j]
            if w <= rem:
                b += p
                rem -= w
            else:
                b += ratio * rem
                rem = 0
            j += 1
        return b

    # max-heap by bound
    heap = []
    # start with level 0, profit 0, weight 0, taken ()
    start_bound = bound(0, 0, 0)
    # push negative bound because heapq is min-heap
    heapq.heappush(heap, (-start_bound, 0, 0, 0, ()))  # (negbound, profit, weight, level, taken_indices)
    best_profit = 0
    best_taken = ()
    while heap:
        negb, profit, weight, level, taken = heapq.heappop(heap)
        b = -negb
        if b <= best_profit:
            continue
        if level >= n:
            continue
        idx, name, w, p, ratio = indexed[level]
        # option 1: take this item if fits
        if weight + w <= capacity:
            new_profit = profit + p
            new_weight = weight + w
            new_taken = taken + (idx,)
            if new_profit > best_profit:
                best_profit = new_profit
                best_taken = new_taken
            new_bound = bound(level + 1, new_profit, new_weight)
            if new_bound > best_profit:
                heapq.heappush(heap, (-new_bound, new_profit, new_weight, level + 1, new_taken))
        # option 2: don't take
        new_bound2 = bound(level + 1, profit, weight)
        if new_bound2 > best_profit:
            heapq.heappush(heap, (-new_bound2, profit, weight, level + 1, taken))

    # best_taken are original indices in 'indexed' order - convert to original items
    selected = [ None ] * len(best_taken)
    for i, orig_idx in enumerate(best_taken):
        # find item in original items list with index orig_idx
        selected[i] = items[orig_idx]
    return best_profit, selected

# Map algorithm keys to functions & readable names
ALGO_MAP = {
    'dp': ('DP Tabulation', dp_tabulation),
    'greedy': ('Greedy (ratio)', greedy_select),
    'memo': ('Memoization (Top-Down DP)', memoization_topdown),
    'pure': ('Pure Recursion', pure_recursive),
    'bnb': ('Branch & Bound', branch_and_bound),
}

# ---------------------
# Flask routes
# ---------------------

@app.route('/')
def index():
    return render_template('index.html', cargos=cargos, algo_map=ALGO_MAP)

@app.route('/add', methods=['POST'])
def add_cargo():
    name = request.form.get('name').strip()
    if not name:
        return redirect(url_for('index'))
    try:
        weight = int(request.form.get('weight'))
        profit = int(request.form.get('profit'))
    except:
        return redirect(url_for('index'))
    cargos.append((name, weight, profit))
    return redirect(url_for('index'))

@app.route('/delete/<string:name>')
def delete_cargo(name):
    global cargos
    cargos = [c for c in cargos if c[0] != name]
    return redirect(url_for('index'))

@app.route('/result', methods=['POST'])
def result():
    capacity = int(request.form.get('capacity', 0))
    algo_key = request.form.get('algorithm', 'dp')
    algo_name, func = ALGO_MAP.get(algo_key, ALGO_MAP['dp'])
    max_profit, selected = func(list(cargos), capacity)

    total_weight = sum(w for _, w, _ in selected)
    # Prepare chart data: keep all cargos for labels even if not selected (for comparison)
    labels = [c[0] for c in cargos]
    profits = [c[2] for c in cargos]
    weights = [c[1] for c in cargos]

    # Also produce selected labels/profits for charts
    sel_labels = [c[0] for c in selected]
    sel_profits = [c[2] for c in selected]

    # order_of_loading: selected (first-to-last)
    order = [c[0] for c in selected]

    return render_template('result.html',
                           algo_key=algo_key,
                           algo_name=algo_name,
                           selected=selected,
                           total_profit=max_profit,
                           total_weight=total_weight,
                           capacity=capacity,
                           labels=labels,
                           profits=profits,
                           weights=weights,
                           sel_labels=sel_labels,
                           sel_profits=sel_profits,
                           order=order)

if __name__ == '__main__':
    webbrowser.open("http://127.0.0.1:5000/")
    app.run(debug=True)
