# GitHub Public Launch Checklist

Use this as the recorded click-through checklist for the BiblionOCR public launch and as a reusable audit list for future repository reviews.

Launch status:

- the repository is now public on GitHub as of `2026-07-07`
- sections 1 through 8 remain the operating baseline for future membership, permissions, and policy checks

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

Explicitly, for each approved person:

1. open the membership request issue
2. confirm whether it is a `Developer Membership Request` or `Content Creator Membership Request`
3. choose the least-permissive approved access level
4. create a pull request that updates `.github/membership-registry.json`
5. add one new object under `members`, for example:

```json
{
	"github_username": "example-user",
	"role": "developer",
	"access_level": "pull_request_only",
	"status": "approved",
	"approved_by": "preachermax",
	"approved_at": "2026-07-07",
	"request_issue": 123
}
```

6. wait for the `Validate Membership Registry` GitHub Action to pass on that pull request
7. merge the pull request
8. only after merge, go to `Settings -> Collaborators and teams` and add the person with the matching GitHub repository role
9. comment on the original issue with the approval result and close it

Permission mapping to use:

- `curated_intake`: registry-only approval path, usually no added repository collaborator role
- `pull_request_only`: registry approval plus normal pull-request contribution, usually no direct write access
- `triage`: add the GitHub `Triage` role
- `write`: add the GitHub `Write` role
- `maintain`: add the GitHub `Maintain` role
- `admin`: add the GitHub `Admin` role

Practical rule:

- if the access level does not correspond to a built-in GitHub collaborator role, record it in the registry but do not grant broader repository permissions just to "match" the label

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

This step is now complete for the current launch.

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

Ongoing note:

- repeat this section after any major repository policy change or access-model change

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