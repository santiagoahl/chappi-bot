from langchain_core.messages import HumanMessage, AIMessage

chat_history =  {
    "messages": [
        HumanMessage(
            content="What is 12.2 divided by 0.5",
            additional_kwargs={},
            response_metadata={},
        ),
        AIMessage(
            content="",
            additional_kwargs={
                "tool_calls": [
                    {
                        "id": "call_0dWXV8OVJgwxGF6PcsT1mLNm",
                        "function": {
                            "arguments": '{"a":12.2,"b":0.5}',
                            "name": "divide",
                        },
                        "type": "function",
                    }
                ],
                "refusal": None,
            },
            response_metadata={
                "token_usage": {
                    "completion_tokens": 22,
                    "prompt_tokens": 352,
                    "total_tokens": 374,
                    "completion_tokens_details": {
                        "accepted_prediction_tokens": 0,
                        "audio_tokens": 0,
                        "reasoning_tokens": 0,
                        "rejected_prediction_tokens": 0,
                    },
                    "prompt_tokens_details": {"audio_tokens": 0, "cached_tokens": 0},
                },
                "model_name": "gpt-4o-2024-08-06",
                "system_fingerprint": "fp_d8864f8b6b",
                "id": "chatcmpl-BXMRPvYRxfyb7aD233fGxkBXp3Vz2",
                "service_tier": "default",
                "finish_reason": "tool_calls",
                "logprobs": None,
            },
            id="run--624ea8dd-fd75-4545-85f4-527b4166ff3e-0",
            tool_calls=[
                {
                    "name": "divide",
                    "args": {"a": 12.2, "b": 0.5},
                    "id": "call_0dWXV8OVJgwxGF6PcsT1mLNm",
                    "type": "tool_call",
                }
            ],
            usage_metadata={
                "input_tokens": 352,
                "output_tokens": 22,
                "total_tokens": 374,
                "input_token_details": {"audio": 0, "cache_read": 0},
                "output_token_details": {"audio": 0, "reasoning": 0},
            },
        ),
    ]
}

if __name__=="__main__":
    print(chat_history["messages"][-1])