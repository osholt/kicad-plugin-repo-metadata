# Official KiCad Addon Metadata Repository

This repository contains the source files used to generate the
[public-facing addons repository](https://gitlab.com/kicad/addons/repository) used by the Plugin
and Content Manager in KiCad.

Please read all instructions at https://dev-docs.kicad.org/en/addons/ before submitting merge
requests to this repository. Submitted packages must meet all of the requirements outlined there.


## Packaging Toolkit

This repository provides a helper tool to make writing package metadata file compliant with
the repository requirements easier. It requires python3 and a number of additional packages
that you can install using command

`python -m pip install -r ci/requirements.txt`

You can run the tool like this:

`python tools/packager.py`

_Note: on platforms where KiCad is bundled with python (Windows, Mac) you should use python
binary from KiCad or otherwise make sure to have wxpython installed._

This tool can perform almost all of the automated checks that this repository runs when you
commit to gitlab or open a merge request. It's a good idea to make sure your metadata file
passes validation locally before you proceed with the merge request.

Additionally it can provide package sha256 hash and exact download/install sizes that you
can copy to the metadata file.

Tool screenshot:

![screenshot](https://i.imgur.com/80tfzw0.png)


## Recommended workflow

This repository has automation designed to prevent errors sneaking into the metadata files.
To take full advantage of it and reduce the time it takes to review your changes, follow
these steps:

1. Prepare package file as described in the [docs](https://dev-docs.kicad.org/en/addons/).
   Note that metadata file inside the package must have only one version object corresponding
   to the package version and it shouldn't have download_* fields populated.

2. Upload the package file to a host of your choice. It must provide a direct download link.
   Github releases page is a good option.

3. Prepare the metadata file for the repository. It's the same as the one inside the package
   but it can have multiple versions. Additionally it must have `download_url`, `download_sha256`,
   `download_size`, `install_size` fields populated. Use the url provided by your package host
   and use Packaging Toolkit to populate the rest.

   _Tip: some editors like VSCode have excellent support for json and will provide error checking
   on the fly and even show field descriptions and autocomplete suggestions when they detect
   "$schema" field._

   Optional: use the Packaging Toolkit to run validation on the metadata file.

4. Make sure your local checkout of the repository is up to date. Do a `git pull --rebase`
   or `git fetch && git rebase origin/main`.

5. Create new branch in your local checkout. If you use the default `main` branch, some steps of
   the validation will not work as intended.

6. Place the metadata file and icon file (if you have one) in your local checkout of this repo under
   `packages/<your.package.id>`. It's important that `<your.package.id>` matches the `identifier`
   field in the metadata file, otherwise validation will fail.

7. Push your local branch to your fork. This will trigger a CI pipeline that will run validation
   of the package. On your fork page on gitlab under `CI/CD -> Pipelines` menu you can view it's results.

   This is what passing pipeline looks like. Clicking on the jobs will display it's logs:

   ![img](https://i.imgur.com/cF1x8iR.png)

8. If the `validate` stage of the pipeline fails then view it's log to find what went wrong, fix the issue,
   update the metadata file (creating new commit or ammending existing one) and push to your fork again.
   This will trigger new pipeline run.

9. Once the `validate` stage passes check the log of the `build` stage which should pass as well.
   It will contain a link to a temporary PCM repository that contains only new/modified packages.

   This is an example of a message you are looking for:

   ![img](https://i.imgur.com/nEPtJcb.png)

   Add that repository to PCM in KiCad and test your package(s) from there.

10. If everything works as expected go ahead and submit the merge request. The validation will be rerun
    in the context of merge request to make sure everything is still correct but if you followed all the
    steps correctly there should be no new issues at this stage.

11. Wait for your merge request to be reviewed by KiCad team.


_Note: after merge request is approved and merged the changes don't immediately reflect in the
official repository in PCM. It may take up to a day for a scheduled job to pull the changes. If the
package(s) still don't appear reach out to KiCad team by filing an issue or through other
[support channels](https://www.kicad.org/about/contact-us/)._
