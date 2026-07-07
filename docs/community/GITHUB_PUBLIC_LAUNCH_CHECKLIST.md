# GitHub Public Launch Checklist

Use this as the final click-through checklist before making the BiblionOCR repository public.

## 1. Confirm Repo State

- Confirm the repository is `preachermax/BiblionOCR`.
- Confirm the default branch is `master`.
- Confirm `master` contains the latest membership workflow and public-facing docs.
- Confirm the only local-only item is `.tools/` and that it is not meant to be published.

## 2. Confirm Public-Facing Docs

Open and spot-check these files on GitHub:

- [README.md](../../README.md)
- [CONTRIBUTING.md](../../CONTRIBUTING.md)
- [CONTENT_POLICY.md](../../CONTENT_POLICY.md)
- [README.md](README.md)
- [MEMBERSHIP.md](MEMBERSHIP.md)

Verify that:

- the introduction video link works
- contribution rules are clear
- content policy is visible
- the membership approval workflow is documented

## 3. Create Labels

In GitHub, go to `Issues -> Labels` and create:

- `membership`
- `developer`
- `content-creator`

## 4. Confirm Issue Forms

In GitHub, go to `Issues -> New issue` and confirm these forms appear:

- `Developer Membership Request`
- `Content Creator Membership Request`

If they do not appear:

- go to `Settings -> General -> Features`
- make sure `Issues` is enabled

## 5. Protect `master`

In GitHub, go to `Settings -> Branches` and configure protection for `master`:

- require pull requests before merging
- require at least 1 approval
- require conversation resolution before merging
- keep direct pushes restricted unless there is a deliberate admin exception
- enable CODEOWNERS review if that option is available

## 6. Apply the Membership Model

Use this operating rule:

- do not grant GitHub access first and document it later

Instead:

1. receive the request through the correct GitHub issue form
2. review it against repo policy
3. approve it by pull request against the registry
4. then apply matching GitHub permissions

Registry file:

- [.github/membership-registry.json](../../.github/membership-registry.json)

Validator workflow:

- [.github/workflows/validate-membership-registry.yml](../../.github/workflows/validate-membership-registry.yml)

## 7. Apply Permissions Conservatively

- Developers: usually `pull_request_only`, `triage`, or `write`
- Content creators: usually `curated_intake` or `pull_request_only`
- Maintainers: only `maintain` or `admin` when truly required

Do not give broad write access to content-only contributors by default.

## 8. Enforce MFA Expectations

- Require or strongly enforce MFA for any account with write-capable access.
- If the repository later moves into a GitHub organization, enable organization-wide 2FA enforcement.

## 9. Make the Repository Public

In GitHub:

1. go to `Settings -> General`
2. scroll to `Danger Zone`
3. choose `Change repository visibility`
4. set the repository to `Public`
5. confirm the repository name when prompted

## 10. Immediate Post-Launch Check

After the visibility change:

- open the repository in a logged-out or private browser window
- verify the README renders correctly
- verify issue forms are visible
- verify branch protection is still active
- review the Security or Dependabot page for the reported vulnerabilities

## GitHub UI Paths

- Labels: `Issues -> Labels`
- Issue forms: `Issues -> New issue`
- Visibility: `Settings -> General -> Danger Zone`
- Branch protection: `Settings -> Branches`
- Collaborators and roles: `Settings -> Collaborators and teams`

## References

- [README.md](../../README.md)
- [CONTRIBUTING.md](../../CONTRIBUTING.md)
- [CONTENT_POLICY.md](../../CONTENT_POLICY.md)
- [MEMBERSHIP.md](MEMBERSHIP.md)