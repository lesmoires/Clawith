# Email Client Compatibility — 2026

## Support Matrix

| Feature | Gmail Web | Gmail Mobile | Apple Mail | Outlook Web | Outlook Desktop |
|---------|-----------|-------------|------------|-------------|-----------------|
| `<style>` in `<head>` | ❌ Stripped | ❌ Stripped | ✅ | ✅ | ❌ Word engine |
| Inline CSS | ✅ | ✅ | ✅ | ✅ | ✅ |
| Flexbox | ✅ | ✅ | ✅ | ✅ | ❌ |
| CSS Grid | ✅ | ✅ | ✅ | ✅ | ❌ |
| `position:absolute` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `@media` queries | ✅ (inlined) | ✅ | ✅ | ✅ | ❌ |
| `data-embed` styles | ⚠️ Partial | ⚠️ Partial | ✅ | ✅ | ❌ |
| Web fonts | ✅ | ⚠️ Partial | ✅ | ⚠️ Partial | ❌ |
| Background images | ⚠️ Partial | ⚠️ Partial | ✅ | ✅ | ⚠️ VML needed |
| Dark mode | ✅ Auto | ✅ Auto | ✅ | ✅ | ❌ |
| Tables for layout | ✅ | ✅ | ✅ | ✅ | ✅ |
| QuickChart PNG | ✅ | ✅ | ✅ | ✅ | ✅ |

## Key Takeaways

1. **Inline CSS is mandatory** — Gmail strips `<style>` blocks for many accounts
2. **Table-based layout is safest** — Only approach that works in Outlook desktop
3. **QuickChart PNG images work everywhere** — Server-rendered, zero compatibility issues
4. **Dark mode is mostly automatic** — Use `data-embed="only"` for custom overrides
5. **No JavaScript, no flexbox, no grid** — Outlook desktop uses Word rendering engine

## Testing Checklist

- [ ] Renders correctly in Gmail web
- [ ] Renders correctly in Gmail mobile (iOS/Android)
- [ ] Renders correctly in Apple Mail
- [ ] Renders correctly in Outlook web
- [ ] Renders correctly in Outlook desktop (if targeting corporate)
- [ ] Dark mode doesn't break chart visibility (transparent bg)
- [ ] All images have alt text
- [ ] Plain text fallback is readable

## Resources

- [CanIEmail.com](https://www.caniemail.com/) — Comprehensive CSS/HTML support matrix
- [Email Bugs](https://github.com/hteumeuleu/email-bugs) — Known rendering issues
- [MJML Compatibility](https://documentation.mjml.io/) — What MJML handles automatically
