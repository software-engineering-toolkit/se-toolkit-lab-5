# Lab setup

- [1. Required steps](#1-required-steps)
  - [1.1. Clean up Lab 4](#11-clean-up-lab-4)
  - [1.2. Set up your fork](#12-set-up-your-fork)
    - [1.2.1. Fork the course instructors' repo](#121-fork-the-course-instructors-repo)
    - [1.2.2. Go to your fork](#122-go-to-your-fork)
    - [1.2.3. Enable issues](#123-enable-issues)
    - [1.2.4. Add a classmate as a collaborator](#124-add-a-classmate-as-a-collaborator)
    - [1.2.5. Protect your `main` branch](#125-protect-your-main-branch)
  - [1.3. Clone your fork](#13-clone-your-fork)
  - [1.4. Set up the environment](#14-set-up-the-environment)
    - [1.4.1. Install dependencies](#141-install-dependencies)
    - [1.4.2. Create the environment files](#142-create-the-environment-files)
    - [1.4.3. Configure the autochecker API credentials](#143-configure-the-autochecker-api-credentials)
  - [1.5. Start the services locally](#15-start-the-services-locally)
  - [1.6. Deploy to your VM](#16-deploy-to-your-vm)
    - [1.6.1. Connect and get the code](#161-connect-and-get-the-code)
    - [1.6.2. Prepare the environment on the VM](#162-prepare-the-environment-on-the-vm)
    - [1.6.3. Start the services on the VM](#163-start-the-services-on-the-vm)
  - [1.7. Verify the deployment](#17-verify-the-deployment)
  - [1.8. Set up the autochecker](#18-set-up-the-autochecker)

## 1. Required steps

> [!NOTE]
> This lab builds on the same tools and setup from Lab 4.
> If you completed Lab 4, most tools are already installed.
> The main changes are: a new repo, new environment variables, and cleaning up old containers.

### 1.1. Clean up Lab 4

> [!IMPORTANT]
> Remove Lab 4 containers and volumes to free up ports and disk space on your VM.

1. [Connect to your VM](../../wiki/vm.md#connect-to-the-vm).
2. To navigate to the Lab 4 project directory,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cd se-toolkit-lab-4
   ```

3. To stop and remove all Lab 4 containers and volumes,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   docker compose --env-file .env.docker.secret down -v
   ```

4. Go back to the home directory:

   ```terminal
   cd ~
   ```

### 1.2. Set up your fork

#### 1.2.1. Fork the course instructors' repo

1. [Fork the course instructors' repo](../../wiki/github.md#fork-a-repo).

   The course instructors' repo [URL](../../wiki/web-development.md#url) is <https://github.com/inno-se-toolkit/se-toolkit-lab-5>.

#### 1.2.2. Go to your fork

1. [Go to your fork](../../wiki/github.md#go-to-your-fork).

   The [URL](../../wiki/web-development.md#url) of your fork should look like `https://github.com/<your-github-username>/se-toolkit-lab-5`.

#### 1.2.3. Enable issues

1. [Enable issues](../../wiki/github.md#enable-issues).

#### 1.2.4. Add a classmate as a collaborator

1. [Add a collaborator](../../wiki/github.md#add-a-collaborator) — your partner from Lab 4.
2. Your partner should add you as a collaborator in their repo.

#### 1.2.5. Protect your `main` branch

1. [Protect a branch](../../wiki/github.md#protect-a-branch).

### 1.3. Clone your fork

1. [Clone your fork](../../wiki/git-vscode.md#clone-the-repository):

   - Replace `<repo-url>` with [`<your-fork-url>`](../../wiki/github.md#your-fork-url).
   - Replace `<repo-name>` with `se-toolkit-lab-5`.

2. [Open in `VS Code` the directory](../../wiki/vs-code.md#open-the-directory):
   `se-toolkit-lab-5`.

3. [Install the recommended `VS Code` extensions](../../wiki/vs-code.md#install-the-recommended-vs-code-extensions).

### 1.4. Set up the environment

#### 1.4.1. Install dependencies

1. [Check that the current directory is `se-toolkit-lab-5`](../../wiki/shell.md#check-the-current-directory-is-directory-name).

2. To install `Python` dependencies,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   uv sync --dev
   ```

#### 1.4.2. Create the environment files

1. To create the local `.env.secret` file,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cp .env.example .env.secret
   ```

2. To create the `Docker` environment file,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cp .env.docker.example .env.docker.secret
   ```

#### 1.4.3. Configure the autochecker API credentials

The ETL pipeline fetches data from the autochecker dashboard API.
You need to set your credentials in both environment files.

1. Open [`.env.secret`](../../.env.example) and set:

   ```text
   AUTOCHECKER_EMAIL=<your-email>@innopolis.university
   AUTOCHECKER_PASSWORD=<your-github-username><your-telegram-alias>
   ```

   Replace:

   - `<your-email>` with your Innopolis University email prefix (e.g., `j.doe`)
   - `<your-github-username>` with your [GitHub username](../../wiki/github.md#your-github-username) (e.g., `johndoe`)
   - `<your-telegram-alias>` with your Telegram alias without the `@` (e.g., `jdoe`)

   Example: if your GitHub username is `johndoe` and your Telegram alias is `jdoe`, the password is `johndoejdoe`.

2. Open `.env.docker.secret` and set the same values:

   ```text
   AUTOCHECKER_EMAIL=<your-email>@innopolis.university
   AUTOCHECKER_PASSWORD=<your-github-username><your-telegram-alias>
   ```

> [!IMPORTANT]
> The credentials must match your autochecker bot registration.
> If you haven't registered with the autochecker bot, see [step 1.8](#18-set-up-the-autochecker).

### 1.5. Start the services locally

1. [Start `Docker`](../../wiki/docker.md#start-docker).

2. To start the services,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   docker compose --env-file .env.docker.secret up --build
   ```

   Wait for the services to start. You should see log output from the `app`, `postgres`, `pgadmin`, and `caddy` containers.

   <details><summary>Troubleshooting</summary>

   <h4>Port conflict (<code>port is already allocated</code>)</h4>

   Stop the process that uses the port, then retry.

   <h4>Containers exit immediately</h4>

   To rebuild all containers from scratch,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   docker compose --env-file .env.docker.secret down -v
   docker compose --env-file .env.docker.secret up --build
   ```

   </details>

3. Open in a browser: `http://localhost:42002/docs`.

   You should see the [`Swagger UI`](../../wiki/swagger.md#what-is-swagger-ui) page with the API documentation.

4. [Authorize](../../wiki/swagger.md#authorize-in-swagger-ui) with the [`API_KEY`](../../wiki/dotenv-docker-secret.md#api_key) from `.env.docker.secret`.

> [!NOTE]
> The database starts empty — there is no seed data.
> All data will be populated by the ETL pipeline in Task 1.

### 1.6. Deploy to your VM

#### 1.6.1. Connect and get the code

1. [Connect to your VM](../../wiki/vm.md#connect-to-the-vm).

2. To clone your fork on the VM,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   git clone <your-fork-url> se-toolkit-lab-5
   ```

   Replace [`<your-fork-url>`](../../wiki/github.md#your-fork-url).

3. To navigate to the project directory,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cd se-toolkit-lab-5
   ```

#### 1.6.2. Prepare the environment on the VM

1. To create the `Docker` environment file,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cp .env.docker.example .env.docker.secret
   ```

2. Edit `.env.docker.secret` and set your autochecker API credentials:

   ```text
   AUTOCHECKER_EMAIL=<your-email>@innopolis.university
   AUTOCHECKER_PASSWORD=<your-github-username><your-telegram-alias>
   ```

   You can use `nano .env.docker.secret` to edit the file.

#### 1.6.3. Start the services on the VM

1. To start the services in [background](../../wiki/operating-system.md#background-process),

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   docker compose --env-file .env.docker.secret up --build -d
   ```

2. To check that the containers are running,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   docker compose --env-file .env.docker.secret ps --format "table {{.Service}}\t{{.Status}}"
   ```

   You should see all four services running with the status `Up`:

   ```terminal
   SERVICE    STATUS
   app        Up 50 seconds
   caddy      Up 49 seconds
   pgadmin    Up 50 seconds
   postgres   Up 55 seconds (healthy)
   ```

   <details><summary>Troubleshooting</summary>

   <h4>Port conflict (<code>port is already allocated</code>)</h4>

   [Clean up `Docker`](../../wiki/docker.md#clean-up-docker), then run the `docker compose up` command again.

   <h4>Containers exit immediately</h4>

   To rebuild all containers from scratch,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   docker compose --env-file .env.docker.secret down -v
   docker compose --env-file .env.docker.secret up --build -d
   ```

   </details>

### 1.7. Verify the deployment

1. Open in a browser: `http://<your-vm-ip-address>:<caddy-port>/docs`. Replace:

   - [`<your-vm-ip-address>`](../../wiki/vm.md#your-vm-ip-address)
   - [`<caddy-port>`](../../wiki/caddy.md#caddy-port)

   You should see the `Swagger UI` page with endpoints including `/pipeline/sync` and `/analytics/`.

2. [Authorize](../../wiki/swagger.md#authorize-in-swagger-ui) with [`API_KEY`](../../wiki/dotenv-docker-secret.md#api_key) from `.env.docker.secret`.

3. Try the `GET /items/` endpoint.

   You should get an empty array `[]` — the database has no data yet.

### 1.8. Set up the autochecker

> [!NOTE]
> Skip this step if you already registered with the autochecker bot in Lab 4.

1. Open in `Telegram`: <https://t.me/auchebot>.
2. Log in.
3. [Set up your VM for the autochecker](../../wiki/vm-autochecker.md#set-up-the-vm-for-autochecker).
