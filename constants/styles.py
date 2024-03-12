STYLE = """

.main {
    @media only screen and (min-width: 1000px) { 
        width: 70% !important;
        margin: 0 auto; /* Center the container */
    }
}

.small-font{
  font-size: 12pt !important;
  transition: font-size 0.3s ease-out;
}

.small-font:hover {
  font-size: 20px !important;
  transition: font-size 0.3s ease-out;
  transition-delay: 1.5s;
}

.group {
  padding-top: 10px;
  padding-left: 10px;
  padding-right: 10px;
  padding-bottom: 10px;
  border: 2px dashed gray;
  border-radius: 20px;
  box-shadow: 5px 3px 10px 1px rgba(0, 0, 0, 0.4) !important;
}

.accordion > button > span{
  font-size: 12pt !important;
}

.accordion {
  border-style: dashed !important;
  border-left-width: 2px !important;
  border-bottom-width: 2.5px !important;
  border-top: none !important;
  border-right: none !important;
  box-shadow: none !important;
}

.no-gap {
    gap: 0px;
}

.no-radius {
    border-radius: 0px;    
}

.textbox-no-label > label > span {
    display: none;
}

.exp-type > span {
    display: none;
}

.conv-type > span {
    display: none;
}

.conv-type .wrap:nth-child(3) {
    width: 167px;
    margin: auto;    
}

button {
    font-size: 10pt !important;
}

h3 {
    font-size: 13pt !important;
}

#control-panel {
    margin-bottom: 30px;
}

#chatbot {
    background-color: white;
    border: 1px solid #ccc;
    padding: 20px;
    box-shadow: 0px 5px 5px rgba(0, 0, 0, 0.3);
    border-radius: 30px;
    height: 80%;
    width: 80%;

    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 1000; /* Or a high enough value to stay on top */    

    @media (max-width: 768px) { /* Adjust this breakpoint as needed */
        width: 95%; 
    }

    @media (prefers-color-scheme: dark) {
        background-color: dimgrey;
    }    
}

#chat-button {
    border-radius: 40px;
    padding: 0px;
    margin: 0px;
    margin-left: 30px;
    margin-right: 30px;
    font-size: 13pt !important;

    @media only screen and (min-width: 500px) { 
        font-size: 10pt;
        margin: 0 auto; /* Center the container */
    }
}

#chatbot-inside {
    height: 100% !important;
    border-width: 1px !important;
    border-color: lightgray !important;
}

#chatbot-txtbox {
    padding-bottom: 25px;
}

#chatbot-bottm {
    padding-left: 10px;
    padding-right: 10px;
}

#chatbot-right-button {
    float: right;
    width: 20px;
    font-size: 17pt;
}

#chatbot-info {
    word-break: break-word;
}

#chatbot-back {
    position: absolute; /* Stay in place even when scrolling */
    z-index: 1000; /* Ensure it's on top of everything else */
    width: 100%;
    height: 100%;
    left: 0px;
    top: 0px;

    opacity: 0;
    visibility: hidden; /* Ensures the element is not interactive */
    transition: opacity 0.5s ease, visibility 0s 0.5s; /* Transition for opacity and delay visibility */
}

#chatbot-back.visible {
    opacity: 1;
    visibility: visible; /* Now visible and interactive */
    transition: opacity 0.5s ease; /* Smooth transition for opacity */
}

.hover-opacity {
  opacity: 0.8;  /* Normal opacity of the element */
  transition: opacity 0.3s ease-in-out;  /* Smooth opacity change */
}

.hover-opacity:hover {
  opacity: 1;  /* Full opacity on hover */
}

.markdown-center {
    text-align: -webkit-center;
}
"""
