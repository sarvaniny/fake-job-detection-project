def load_css():

    return """
    <style>

    /* App background */

    .stApp {
        background: linear-gradient(
            135deg,
            #ff6f91,
            #ff9671,
            #ffc75f
        );
    }

    /* main container */

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1100px;
    }

    /* iOS style card */

    .card {

        background: #fff4ec;
        border-radius: 18px;

        padding: 24px;
        margin-bottom: 22px;

        box-shadow:
        0 10px 25px rgba(0,0,0,0.12);

    }

    /* section title */

    .card h2 {
        margin-top: 0;
    }

    /* signal badge */

    .badge {

        display: inline-block;

        padding: 6px 14px;
        margin: 4px;

        border-radius: 999px;

        background: #ffe0d3;

        font-size: 14px;
        font-weight: 500;

    }

    /* button */

    div.stButton > button {

        background: linear-gradient(
            45deg,
            #ff6f91,
            #ff9671
        );

        color: white;

        border-radius: 10px;
        border: none;

        padding: 10px 22px;

        font-weight: 600;

    }

    </style>
    """