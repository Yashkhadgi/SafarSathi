# Design rules (must follow for every UI change)

Goal: the site must not look like a generic AI-generated product.

Never use:
- purple gradients (or any decorative gradient backgrounds)
- pill-shaped buttons (use a small radius, 6 to 8px)
- fake reviews, fake testimonials, fake metrics, fake customer counters
- vague hero text (every headline must say what the product does, specifically)
- emoji as icons (use one consistent SVG icon set, e.g. lucide)
- em dashes in any user-facing text (use commas, periods or colons)
- over-the-top scroll animation, parallax, scroll-jacking
- cursor animations or custom cursors
- AI-generated photos or illustrations. Use real product screenshots, or no imagery.
- AI-sounding copy: no "revolutionize", "seamless", "unlock", "empower", "elevate", "journey" filler. Plain, specific sentences.

Always:
- Solid colours, one accent colour, high contrast. Self-hosted fonts, max two families.
- Motion: only small state transitions (150 to 200ms), respect prefers-reduced-motion.
- Visible keyboard focus, labelled controls, 4.5:1 contrast minimum.
- Honest empty states and error messages.
- Real copy about the product's actual features only.

Launch gate (do not launch until all are true):
- custom domain connected with HTTPS
- favicon set added (ico, svg, apple-touch-icon, PWA icons)
- no "Made with ..." or "Built with ..." badge anywhere (including Gradio or template footers)
- Privacy Policy page and Terms and Conditions page published, matching real data practices

Before finishing any task: re-check this whole list against the code and report any rule you could not satisfy. Do not claim a rule is met without checking.
