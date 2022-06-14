class ABShaders:
    vertex_shader_simple = '''
            in vec3 position;
            in vec4 color;
            uniform mat4 perspective_matrix;
            uniform mat4 object_matrix;
            uniform float point_size;
            uniform float alpha_radius;
            out vec4 f_color;
            out float f_alpha_radius;
            void main()
            {
                gl_Position = perspective_matrix * object_matrix * vec4(position, 1.0f);
                gl_PointSize = point_size;
                // f_color = color;
                f_color = vec4(color[0], color[1], color[2], color[3]);
                f_alpha_radius = alpha_radius;
            }
        '''

    fragment_shader_simple = '''
            in vec4 f_color;
            in float f_alpha_radius;
            out vec4 fragColor;
            void main()
            {
                float r = 0.0f;
                float a = 1.0f;
                vec2 cxy = 2.0f * gl_PointCoord - 1.0f;
                r = dot(cxy, cxy);
                if(r > f_alpha_radius){
                    discard;
                }
                fragColor = f_color * a;
            }
       '''