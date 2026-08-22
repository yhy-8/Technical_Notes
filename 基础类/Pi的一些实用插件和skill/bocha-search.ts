import { Type } from "typebox";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";


// ==============================
// 博查 API Key
// ==============================

const BOCHA_API_KEY = "你的key";


// ==============================
// Pi Extension
// ==============================

export default function (pi: ExtensionAPI) {


    pi.registerTool({

        name: "bocha_search",

        label: "Bocha Web Search",


        description: `

Search the web using Bocha Search.

Use this tool when:
- latest information is required
- user asks about current information
- internal knowledge may be outdated
- external references are needed


You can control:
- search keywords
- freshness/time range
- result count
- include websites
- exclude websites
- summaries

        `,


        parameters: Type.Object({


            query: Type.String({

                description:
                "Search keywords"

            }),



            freshness: Type.Optional(

                Type.String({

                    description:
                    `
Time range.

Available:
- noLimit
- oneDay
- oneWeek
- oneMonth
- oneYear

`

                })

            ),



            count: Type.Optional(

                Type.Number({

                    description:
                    "Number of results, 1-50"

                })

            ),



            summary: Type.Optional(

                Type.Boolean({

                    description:
                    "Whether return webpage summary"

                })

            ),



            include: Type.Optional(

                Type.Array(

                    Type.String(),

                    {

                    description:
                    "Only search specified websites"

                    }

                )

            ),



            exclude: Type.Optional(

                Type.Array(

                    Type.String(),

                    {

                    description:
                    "Exclude specified websites"

                    }

                )

            )


        }),




        async execute(toolCallId, params) {


            if(!BOCHA_API_KEY)
            {

                throw new Error(
                    "Bocha API key missing"
                );

            }



            // ==========================
            // 构造请求
            // ==========================


            const requestBody:any = {


                query:
                params.query,


                count:
                params.count ?? 10,


                freshness:
                params.freshness ?? "noLimit",


                summary:
                params.summary ?? true


            };



            if(params.include)
            {

                requestBody.include =
                    params.include.join("|");

            }



            if(params.exclude)
            {

                requestBody.exclude =
                    params.exclude.join("|");

            }



            // ==========================
            // 请求博查
            // ==========================


            const response =
                await fetch(

                    "https://api.bochaai.com/v1/web-search",

                    {

                    method:"POST",


                    headers:{


                        "Authorization":
                        `Bearer ${BOCHA_API_KEY}`,


                        "Content-Type":
                        "application/json"


                    },


                    body:
                    JSON.stringify(requestBody)


                    }

                );



            if(!response.ok)
            {

                // 附带 API 返回的错误详情（如 Missing parameter query）
                let errorDetail = "";

                try
                {

                    const errorBody =
                        await response.json();

                    errorDetail =
                        errorBody.message ?? errorBody.msg ?? "";

                }
                catch
                {

                    // 响应体不是 JSON 时忽略详情

                }

                throw new Error(

                    `Bocha API Error: ${response.status}`

                    + (errorDetail ? ` - ${errorDetail}` : "")

                );

            }



            const data =
                await response.json();




            // ==========================
            // 提取结果
            // ==========================


            // API 返回结构: { code, data: { webPages: { value: [...] } } }
            // 必须穿透两层 data 才能取到结果列表
            const pages =
                data.data?.webPages?.value ?? [];



            if(pages.length===0)
            {

                return {

                    content:[

                        {

                        type:"text",

                        text:
                        "No results found."

                        }

                    ]

                };

            }




            // ==========================
            // 格式化给 AI
            // ==========================


            const resultText =

                pages.map(

                    (item:any,index:number)=>{


return `

## ${index+1}. ${item.name ?? "No title"}


URL:
${item.url ?? ""}


Source:
${item.siteName ?? ""}


Time:
${item.datePublished ?? ""}


Summary:
${item.summary ?? item.snippet ?? "No summary"}

`;

                    }

                ).join("\n");





            return {


                content:[

                    {

                    type:"text",

                    text:
                    resultText

                    }

                ]

            };


        }


    });


}