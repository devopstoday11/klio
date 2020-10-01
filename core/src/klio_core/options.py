# Copyright 2020 Spotify AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import click


#####
# utils for options
#####
class MutuallyExclusiveOption(click.Option):
    """
    Helper class to validate and document mutual exclusivity between options.

    This unfortunately doesn't work with click arguments (only options).

    To use, pass in both of the following keywords into an option declaration:
        click.option(
            "--an-option"
            cls=MutuallyExclusiveOption
            mutually_exclusive=["string_of_exclusive_option", "another_option"]
        )
    """

    def __init__(self, *args, **kwargs):
        self.mut_ex_opts = set(kwargs.pop("mutually_exclusive", []))
        help_text = kwargs.get("help", "")
        if self.mut_ex_opts:
            mutex = [self._varname_to_opt_flag(m) for m in self.mut_ex_opts]
            mutex_fmted = ["``{}``".format(m) for m in mutex]
            ex_str = ", ".join(mutex_fmted)
            kwargs["help"] = help_text + (
                "\n\n**NOTE:** This option is mutually exclusive with "
                "[{}].".format(ex_str)
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    @staticmethod
    def _varname_to_opt_flag(var):
        return "--" + var.replace("_", "-")

    def handle_parse_result(self, ctx, opts, args):
        if self.mut_ex_opts.intersection(opts) and self.name in opts:
            mutex = [
                "`" + self._varname_to_opt_flag(m) + "`"
                for m in self.mut_ex_opts
            ]
            mutex = ", ".join(mutex)
            msg = "Illegal usage: `{}` is mutually exclusive with {}.".format(
                self._varname_to_opt_flag(self.name), mutex
            )
            raise click.UsageError(msg)

        return super(MutuallyExclusiveOption, self).handle_parse_result(
            ctx, opts, args
        )


def _verify_gcs_uri(ctx, param, value):
    if value and not value.startswith("gs://"):
        raise click.BadParameter(
            "Unsupported location type. Please provide a GCS location with "
            "the `gs://` prefix."
        )

    return value


#####
# common options
#####
def job_dir(*args, **kwargs):
    mutually_exclusive = kwargs.get("mutex", [])

    def wrapper(func):
        return click.option(
            "-j",
            "--job-dir",
            type=click.Path(exists=True),
            help=(
                "Job directory where the job's ``Dockerfile`` is located. "
                "Defaults current working directory."
            ),
            cls=MutuallyExclusiveOption,
            mutually_exclusive=mutually_exclusive,
        )(func)

    # allows @options.foo to be used without parens (i.e. no need to do
    # `@options.foo()`) when there are no args/kwargs provided
    if args:
        return wrapper(args[0])
    return wrapper


def config_file(*args, **kwargs):
    mutually_exclusive = kwargs.get("mutex", [])

    def wrapper(func):
        return click.option(
            "-c",
            "--config-file",
            type=click.Path(exists=False),
            help=(
                "Path to config filename. If ``PATH`` is not absolute, it "
                "will be treated relative to ``--job-dir``. Defaults to "
                "``klio-job.yaml``."
            ),
            cls=MutuallyExclusiveOption,
            mutually_exclusive=mutually_exclusive,
        )(func)

    # allows @options.foo to be used without parens (i.e. no need to do
    # `@options.foo()`) when there are no args/kwargs provided
    if args:
        return wrapper(args[0])
    return wrapper


def override(func):
    return click.option(
        "-O",
        "--override",
        default=[],
        multiple=True,
        help="Override a config value, in the form ``key=value``.",
    )(func)


def template(func):
    return click.option(
        "-T",
        "--template",
        default=[],
        multiple=True,
        help=(
            "Set the value of a config template parameter"
            ", in the form ``key=value``.  Any instance of ``${key}`` "
            "in ``klio-job.yaml`` will be replaced with ``value``."
        ),
    )(func)
