import anthropic
import sqlite3

def get_campaign_data(campaign_id):
    conn = sqlite3.connect('sentrify.db')
    c = conn.cursor()
    c.execute('SELECT company_name, campaign_name, template, created_at FROM campaigns WHERE id = ?', (campaign_id,))
    campaign = c.fetchone()
    c.execute('SELECT email, clicked_at, training_completed FROM results WHERE campaign_id = ?', (campaign_id,))
    results = c.fetchall()
    conn.close()
    return campaign, results

def analyse_campaign(campaign_id):
    campaign, results = get_campaign_data(campaign_id)
    if not campaign:
        return "Campaign not found."

    company_name = campaign[0]
    campaign_name = campaign[1]
    template = campaign[2]
    total = len(results)
    trained = sum(1 for r in results if r[2] == 1)
    not_trained = total - trained
    training_rate = (trained / max(total, 1)) * 100

    # Build employee list for AI context
    employee_list = ""
    for r in results:
        status = "completed training" if r[2] == 1 else "did not complete training"
        employee_list += f"- {r[0]} clicked the link and {status}\n"

    prompt = f"""
You are a cybersecurity risk analyst reviewing the results of a phishing simulation campaign run by Sentrify, Africa's human risk management platform.

Here are the campaign details:

Company: {company_name}
Campaign Name: {campaign_name}
Phishing Template Used: {template}
Total Employees Who Clicked: {total}
Completed Training After: {trained} ({training_rate:.0f}%)
Did Not Complete Training: {not_trained}

Employee Results:
{employee_list}

Please provide a professional security risk assessment that includes:
1. A brief summary of the campaign results
2. The risk level for this organisation (Low / Medium / High / Critical)
3. Key observations about employee behaviour
4. Specific actionable recommendations for improving security awareness
5. A compliance note relevant to Nigerian businesses (NDPR, CBN guidelines)

Write in clear, plain English that a non-technical business owner can understand. Be direct and specific. Keep it under 400 words.
"""

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text

if __name__ == '__main__':
    result = analyse_campaign(1)
    print(result)
