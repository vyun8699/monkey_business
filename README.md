# monkey_business
 
Project Repository by Kiran Sunil (@PsychJoker) and Vincent Yunansan (@vyun8699)

Run on Python 3.11.9

## Streamlit: 
Go to streamlit subfolder and run in CL: streamlit run main.py
Streamlit has been abandoned now since it is inefficient

## Node.JS:
Was considered but Node.JS is asynchronious and shouldn't be used for processes that require CPU (such as EDA)

## React:
Major issues trying to get react to work. This is what I did:

>> Install node: brew install node
>> Try to create app: npx create-react-app client

if the above doesn't work, do this:

>> npx create-react-app client --legacy-peer-deps
>> npx create-react-app client --force

Both above didn't work for me

So I did this:

>> npx create-react-app client
>> cd client
>> npm install react@^18.0.0 react-dom@^18.0.0
>> npm install -g npm@latest
>> npm install web-vitals
>> npm start