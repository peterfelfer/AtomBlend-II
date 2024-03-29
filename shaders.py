class ABShaders:
    # shaders for drawing the bounding box / metric
    metric_vertex_shader = '''
        //in vec3 position;
        //in vec4 color;
        //uniform mat4 projection_matrix;
        //uniform mat4 object_matrix;
        //uniform mat4 view_matrix;
        //out vec4 f_color;

        void main(){
            gl_Position = projection_matrix * object_matrix * vec4(position, 1.0f);
            f_color = color;
        }

    '''
    metric_fragment_shader = '''
        //in vec4 f_color;
        //out vec4 fragColor;
        void main(){
            fragColor = f_color;
        }
    '''

    # shaders for the rendering of the atoms
    vertex_shader_simple = '''
            //in vec3 position;
            //in vec4 color;
            //in float ps;
            //uniform mat4 projection_matrix;
            //uniform mat4 object_matrix;
            //out vec4 f_color;
            //out float f_alpha_radius;
            void main()
            {
                gl_Position = projection_matrix * object_matrix * vec4(position, 1.0f);
                gl_PointSize = ps;
                f_color = vec4(color[0], color[1], color[2], color[3]);
                f_alpha_radius = 1.0;
            }
    '''

    fragment_shader_simple = '''
            //in vec4 f_color;
            //in float f_alpha_radius;
            //out vec4 fragColor;
            void main()
            {
                float r = 0.0f;
                float d = 0.0f;
                float a = 1.0f;
                vec2 cxy = 2.0f * gl_PointCoord - 1.0f;
                r = dot(cxy, cxy);
                d = fwidth(r);
                a = 1.0 - smoothstep(1.0 - (d / 2), 1.0 + (d / 2), r);
                if(r > 0.6){
                    discard;
                }
                fragColor = vec4(f_color.rgb, f_color.a * a);
            }
    '''

    # shaders for the rendering of the legend
    legend_vertex_shader = '''
            //in vec3 position;
            //in vec4 color;
            //in float ps;
            //uniform mat4 projection_matrix;
            //uniform mat4 object_matrix;
            //out vec4 f_color;
            //out float f_alpha_radius;
            void main()
            {
                gl_Position = vec4(position, 1.0f);
                gl_PointSize = ps;
                f_color = vec4(color[0], color[1], color[2], color[3]);
                f_alpha_radius = 1.0;
            }
    '''

    legend_fragment_shader = '''
            //in vec4 f_color;
            //in float f_alpha_radius;
            //out vec4 fragColor;
            void main()
            {
                float r = 0.0f;
                float d = 0.0f;
                float a = 1.0f;
                vec2 cxy = 2.0f * gl_PointCoord - 1.0f;
                r = dot(cxy, cxy);
                d = fwidth(r);
                a = 1.0 - smoothstep(1.0 - (d / 2), 1.0 + (d / 2), r);
                if(r > 0.6){
                    discard;
                }
                fragColor = vec4(f_color.rgb, f_color.a * a);
            }
    '''
