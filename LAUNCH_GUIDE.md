# Getting Rootly onto phones

This guide assumes you have never done this before. There are four stages.
Each one needs an account that only you can create, because they are tied to
your name, email and (for Apple and Google) your payment card.

You don't need to change any code. Where a step says "tell Claude", open a
Claude Code session on this repository and paste what it asks for.

## Stage 1: Get a plant database key (5 minutes, free)

1. Go to https://trefle.io and create an account.
2. Copy the "access token" it gives you. Keep it somewhere safe; you need it in stage 2.

Without this the app still works, but searching only finds the three sample plants.

## Stage 2: Put the server online (about 20 minutes)

The phone app needs the Rootly server to be on the internet, not on your laptop.
The repository is set up for a hosting company called Render.

1. Go to https://render.com and sign up using "Sign in with GitHub".
2. Choose **New**, then **Blueprint**, and pick the `cleaned_rootly` repository.
3. Render reads the file `render.yaml` and shows a web service called `rootly`
   and a database called `rootly-db`. It asks for two values:
   - `TREFLE_API_KEY`: paste the token from stage 1.
   - `CONTACT_EMAIL`: an email address people can write to about their data.
4. Press **Apply** and wait until the service says "Live".
5. Render shows the address of your site, something like
   `https://rootly-abcd.onrender.com`. Open it: you should see the Rootly homepage.

Things to know:

- `render.yaml` asks for Render's free plans. Free plans have limits (the site
  goes to sleep when unused, and free databases are deleted after a period).
  Check Render's pricing page and move both to a paid plan before real people rely on the app.
- The blueprint must point at the branch that has this code. If the code has
  not been merged into `main` yet, pick the branch in Render's Blueprint screen.

**Then tell Claude:** "My Rootly server address is https://...". Claude puts
it in `mobile/.env`, which is how the app knows where the server is.

## Stage 3: Try the app on your own phone (about 30 minutes)

This uses a free service called Expo that builds the app in the cloud, so you
don't need a Mac.

One-time set-up on your laptop:

1. Install Node.js from https://nodejs.org (choose the "LTS" download).
2. Create a free account at https://expo.dev.
3. Open the Terminal app (Mac) or PowerShell (Windows) and go to the app's folder:

   ```bash
   cd path/to/cleaned_rootly/mobile
   ```

4. Install the app's parts and the Expo build tool:

   ```bash
   npm install
   ```

   ```bash
   npm install -g eas-cli
   ```

5. Log in and connect the project to your Expo account (answer yes to its questions):

   ```bash
   eas login
   ```

   ```bash
   eas init
   ```

Build a version you can install on an Android phone:

```bash
eas build --platform android --profile preview
```

After about 15 minutes it prints a link and a QR code. Open it on an Android
phone to install the app.

For an iPhone you need the Apple account from stage 4 first, then:

```bash
eas build --platform ios --profile preview
```

Check on a real phone: sign up, add a plant, take a photo of it, add a
reminder for tomorrow and see that the notification arrives at 9 in the morning.
These are the parts that could not be tested without a phone.

## Stage 4: Publish to the stores

| | Apple App Store | Google Play |
| --- | --- | --- |
| Account | https://developer.apple.com/programs ($99 a year) | https://play.google.com/console ($25 once) |
| Build | `eas build --platform ios --profile production` | `eas build --platform android --profile production` |
| Upload | `eas submit --platform ios` | `eas submit --platform android` |

Both stores then ask you to fill in a listing. You will need:

- **Screenshots** of the app (take them on your phone).
- **A description** of what the app does.
- **A privacy policy link**: use `https://your-server-address/privacy`.
  Read that page first and make sure it is true for you.
- **Account deletion** (both stores require it): in the app it is under
  Account, and on the web at `https://your-server-address/account`.
- **Data safety / privacy questions**: Rootly collects a name, an email
  address, photos and the plant data people enter. It has no adverts and no tracking.

Review usually takes a few days. Google also requires new personal developer
accounts to run a closed test with a group of testers before going public;
the Play Console walks you through it.

## About the name

"Rootly" is already the name of another company's software product. Before
you publish, search both stores and consider a different app name; a clash
can get a listing rejected or removed. The name shown to people is one line
in `mobile/app.json`, so it is easy to change.

## When something changes

After any change to the app, run the same `eas build` and `eas submit`
commands again. The server updates itself: Render redeploys when new code
reaches the branch it watches.
