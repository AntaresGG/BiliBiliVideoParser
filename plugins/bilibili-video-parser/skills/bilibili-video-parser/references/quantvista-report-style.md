# QuantVista HTML Report Style

Use this reference when the user asks for a report matching `0M1-QuantVista`.

## Palette

```css
:root {
  --bg-base: #f4f1ea;
  --bg-surface: #ffffff;
  --bg-ink: #1a1b1e;
  --card-bg: rgba(255, 255, 255, 0.86);
  --card-border: rgba(31, 32, 35, 0.07);
  --accent-primary: #c65a2e;
  --accent-secondary: #2e6a7a;
  --accent-tertiary: #5b3f8c;
  --status-success: #15803d;
  --status-error: #b91c1c;
  --status-warning: #d97706;
  --market-neutral: #64748b;
}
```

## Structure

For investment research reports, prefer:

1. topbar with product/research identity;
2. hero with thesis, one strong verdict, and KPI tiles;
3. one-page conclusion cards;
4. signal matrix table;
5. timeline / catalyst calendar;
6. detailed thesis cards;
7. scenario analysis;
8. execution checklist;
9. source/disclaimer footer.

Use cards for repeated items and framed analytical modules. Avoid nested cards. Keep radius close to the project style, but standalone reports may use `10px` to `16px` for editorial readability.

## Tone

- Use concise Chinese.
- Prefer "交易窗口", "验证指标", "失效条件", "执行清单".
- Avoid promotional language and overconfident calls.
- Make action conditions explicit.
