# Security policy

climon is a non-commercial hobby project provided AS IS, with no warranty (see `README.md`
and `legal/`). Even so, security reports are welcome and appreciated.

## Reporting a vulnerability

Please do **not** open a public issue for a security problem.

Instead, use GitHub's private vulnerability reporting:
**Security tab -> "Report a vulnerability"** on this repository. That channel is private and
goes only to the maintainer.

Include what you found, how to reproduce it, and the impact you expect. There is no bounty,
but credit is happily given if you would like it.

## Scope

The main internet-facing surface is the optional online battle server
(`src/climon/server/`). It is authoritative and anonymous: it holds no accounts, passwords,
payment data, or personal data beyond a transient in-memory display name, and it bounds
connections and message sizes. The client (the terminal game) reads only local config and
renders battles.

## Out of scope

- Denial of service from a single abusive client beyond the built-in connection/size caps
  (edge rate-limiting is a deployment concern).
- The bundled Pokemon assets and names (an intellectual-property matter, not a security one;
  see `legal/DISCLAIMER.md`).
