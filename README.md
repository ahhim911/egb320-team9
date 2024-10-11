# Welcome to EGB320 Team 9 Codespace

This codespace is for EGB320 team 9 teammates. We learned from the resources from QUT Robotics Club - Robotics101, and thanks to all the contributors and teachers.

## Instructions to Clone from Git

After you SSH to your Raspberry Pi or connect it to a monitor and keyboard/mouse, you can clone this repo to start your happy coding journey.

To clone this codespace to your Raspberry Pi, you first need to install `git` on your Pi. Please run this command in the terminal:

```bash
sudo apt install git
```

After installing Git, you can clone this codespace to your target directory:

```bash
cd YourTargetDirectory
git clone https://github.com/ahhim911/egb320-team9.git
```

Then you should see this on your terminal:

```
Cloning into 'egb320-team9'...
remote: Enumerating objects: 27, done.
remote: Counting objects: 100% (27/27), done.
remote: Compressing objects: 100% (24/24), done.
remote: Total 27 (delta 2), reused 0 (delta 0), pack-reused 0
Receiving objects: 100% (27/27), 15.03 KiB | 641.00 KiB/s, done.
Resolving deltas: 100% (2/2), done.
```

Check the directory with:

```bash
ls
```

It should show:

```
egb320-team9
```

Done! You have cloned this repo. Happy Coding!

## Instructions to Pull Changes

To keep your local repository up-to-date with the latest changes from the remote repository, you should regularly pull changes. Use the following command:

```bash
git pull origin main
```

This will fetch and merge changes from the `main` branch of the remote repository into your local repository.

## Instructions to Push Changes

When you have made changes to the code and are ready to upload them to the remote repository, follow these steps:

1. **Add Changes**: Stage the files you want to commit. You can add all changed files with:

   ```bash
   git add .
   ```

   Or, add specific files by specifying their names:

   ```bash
   git add filename1 filename2
   ```

2. **Commit Changes**: Commit your changes with a meaningful message:

   ```bash
   git commit -m "Your descriptive commit message"
   ```

3. **Push Changes**: Push your committed changes to the remote repository:

   ```bash
   git push origin main
   ```

Make sure you have the necessary permissions to push to the repository. If you encounter any issues, check that your SSH key is correctly set up and added to your GitHub account.

## Additional Resources

- [GitHub SSH Key Setup Guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [Git Basics: Getting a Git Repository](https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository)

Happy Coding! If you have any questions or need further assistance, feel free to reach out to the team.

# Package to be install
## Opencv
Use this code to install Opencv
```
sudo apt-get install python3-opencv
```

## Numpy
```
sudo apt-get install libopenblas-dev
pip uninstall numpy
pip install numpy==1.26.4
```

## Pandas
```
pip install pandas
```




