# commits from users that match against the given string will be included
useremail = [ "someone", ]
# output directory, where the tarballs for respective months will be stored
output_dir = "somewhere"
# list of repositories (git clone paths) to be analyzed
repository = [ "somerepo", ]
# if repository dir is specified, repositories are first looked in the directory, if not found, they are downloaded into a temp directory
repository_dir = "somedir"

# month and year since which the tarball should be generated
since = (2016,2)
till = ()
