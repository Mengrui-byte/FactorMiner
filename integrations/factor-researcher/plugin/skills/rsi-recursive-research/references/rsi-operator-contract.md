# RSI Operator Contract

`RMA(x, n)` is Wilder's recursive moving average, seeded by the arithmetic mean of the first complete `n` observations and updated with `alpha = 1/n`.

`RSI(close, n)` computes positive and negative close-to-close changes, applies the same Wilder average to gains and losses, and returns:

```text
100 - 100 / (1 + average_gain / average_loss)
```

Required behavior:

- leading warm-up values are null/NaN until a complete seed exists;
- all-up windows return 100, all-down windows return 0, and flat windows return 50;
- non-finite input resets the state and cannot bridge a missing-data gap;
- appending future observations cannot change already computed history;
- implementation must agree with an independent reference on published fixtures;
- no RSI threshold, sign, or horizon may be selected using the sealed test period.
